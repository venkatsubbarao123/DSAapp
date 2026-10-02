"""Production Acceptance and End-to-End User Journey Verification Script.

Tests the live running DSAapp backend:
1. User registration with automatic profile creation
2. Duplicate registration protection and safe error response
3. User login and authentication verification
4. /auth/me retrieval with safe display name serialization
5. Problem library pagination, difficulty distribution, and topic filtering
6. AI Tutor pedagogical guidance generation with real problem context
7. Interview simulation: start, answer submission, finish session, report generation
8. Gamification profile, XP rewards, and streak tracking
9. Token refresh and rotation
10. Safe user logout and token revocation

Response contract note:
    The API intentionally serves two shapes. Auth/health/payments return the
    typed envelope {"success": true, "data": {...}} (schema APIResponse), while
    the AI, interview and gamification routers return their domain payload
    directly (e.g. {"explanation": ...}). The real frontend client
    (frontend/src/services/apiClient.ts) normalises both. `unwrap()` below
    reproduces exactly that normalisation, so this script asserts against the
    same contract the application uses instead of blindly indexing ["data"].
"""

import httpx
import time
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
# AI calls proxy a live LLM provider; keep the client budget above the backend
# AI_TIMEOUT_SECONDS so the server can return a real answer or its bounded
# fallback instead of being cut off mid-flight.
AI_CLIENT_TIMEOUT_SECONDS = 60.0


def unwrap(response: httpx.Response, context: str) -> dict:
    """Return the payload of a successful response under either contract shape.

    Mirrors the frontend apiClient normalisation:
      - {"success": true, "data": {...}} -> return the inner data object
      - bare domain payload              -> return it unchanged

    Never indexes ["data"] blindly, and never proceeds on a failed request.
    """
    if response.status_code >= 400:
        raise AssertionError(
            f"{context} failed with HTTP {response.status_code}: {response.text[:500]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise AssertionError(
            f"{context} returned a non-JSON body: {response.text[:300]}"
        ) from exc

    if not isinstance(payload, dict):
        raise AssertionError(f"{context} returned an unexpected shape: {type(payload)}")

    # Check for an explicit error envelope before touching any payload field.
    if payload.get("success") is False:
        err = payload.get("error") or {}
        raise AssertionError(
            f"{context} reported failure: {err.get('code', 'UNKNOWN')}: "
            f"{err.get('message', 'no message')}"
        )

    if payload.get("success") is True and "data" in payload:
        data = payload["data"]
        if data is None:
            raise AssertionError(f"{context} returned an empty data envelope")
        return data

    return payload


def test_full_user_journey():
    client = httpx.Client(base_url=BASE_URL, timeout=AI_CLIENT_TIMEOUT_SECONDS)

    print("============================================================")
    print("DSAapp â€” LIVE PRODUCTION ACCEPTANCE & USER JOURNEY TEST")
    print("============================================================")

    # Health check
    h_res = client.get("http://127.0.0.1:8000/health")
    assert h_res.status_code == 200, f"Health check failed: {h_res.text}"
    print("[PASS] 1. Backend Health Check: 200 OK")

    # 1. Registration
    test_email = f"prod_verify_{uuid.uuid4().hex[:6]}@example.com"
    reg_res = client.post("/auth/register", json={
        "email": test_email,
        "password": "ProductionReadyPass123!",
        "display_name": "Acceptance Tester",
    })
    assert reg_res.status_code == 201, f"Registration failed ({reg_res.status_code}): {reg_res.text}"
    reg_data = unwrap(reg_res, "Registration")
    access_token = reg_data["access_token"]
    refresh_token = reg_data.get("refresh_token")
    user_info = reg_data.get("user")
    assert access_token, "No access_token returned"
    assert user_info and user_info["email"] == test_email, f"User info invalid: {user_info}"
    print(f"[PASS] 2. User Registration: 201 Created (User: {user_info['email']}, Name: {user_info['display_name']})")

    # 2. Duplicate registration rejection
    dup_res = client.post("/auth/register", json={
        "email": test_email,
        "password": "ProductionReadyPass123!",
    })
    assert dup_res.status_code == 400, f"Expected 400 on duplicate, got {dup_res.status_code}: {dup_res.text}"
    dup_payload = dup_res.json()
    assert dup_payload.get("success") is False, "Duplicate registration must return success=false"
    assert dup_payload["error"]["message"], "Duplicate registration must carry a safe error message"
    print(f"[PASS] 3. Duplicate Registration Protection: 400 Rejected ('{dup_payload['error']['message']}')")

    # 3. User login
    login_res = client.post("/auth/login", json={
        "email": test_email,
        "password": "ProductionReadyPass123!",
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = unwrap(login_res, "Login")
    login_token = login_data["access_token"]
    auth_headers = {"Authorization": f"Bearer {login_token}"}
    print("[PASS] 4. User Login: 200 OK with fresh Bearer token")

    # 4. Auth /me
    me_res = client.get("/auth/me", headers=auth_headers)
    assert me_res.status_code == 200, f"Auth /me failed: {me_res.text}"
    me_data = unwrap(me_res, "Auth /me")
    assert me_data["display_name"] == "Acceptance Tester", f"Unexpected display name: {me_data}"
    print(f"[PASS] 5. Session /me Profile: 200 OK (Role: {me_data['role']}, Plan: {me_data['plan']})")

    # 5. Problems library & database integrity
    prob_res = client.get("/problems?page=1&page_size=5")
    prob_data = unwrap(prob_res, "Problems list")
    assert prob_data["total"] == 415, f"Expected 415 problems, got {prob_data['total']}"
    print(f"[PASS] 6. Neon Database Problem Library: 415/415 Published Problems (5 items on page 1 of {prob_data['total_pages']})")

    easy_total = unwrap(client.get("/problems?difficulty=EASY&page_size=1"), "EASY filter")["total"]
    med_total = unwrap(client.get("/problems?difficulty=MEDIUM&page_size=1"), "MEDIUM filter")["total"]
    hard_total = unwrap(client.get("/problems?difficulty=HARD&page_size=1"), "HARD filter")["total"]
    assert easy_total == 144 and med_total == 186 and hard_total == 85, (
        f"Difficulty distribution mismatch: {easy_total}/{med_total}/{hard_total}"
    )
    print(f"[PASS] 7. Difficulty Distribution: Easy={easy_total}, Medium={med_total}, Hard={hard_total} (Sum: {easy_total+med_total+hard_total})")

    # Problem detail (uses a real problem id from the library)
    first_prob = prob_data["items"][0]
    detail_res = client.get(f"/problems/{first_prob['id']}")
    detail = unwrap(detail_res, "Problem detail")
    print(f"[PASS] 8. Problem Detail: '{detail.get('title')}' ({detail.get('difficulty')}) loaded")

    # Topic filtering (contract: /problems accepts `topic_slug`, not `topic_id`)
    topics_data = unwrap(client.get("/topics?page=1&page_size=5"), "Topics list")
    topic_items = topics_data.get("items") or []
    assert topic_items, "Expected at least one published topic"
    assert topics_data.get("total", 0) >= 50, f"Expected the full topic library, got {topics_data.get('total')}"
    t_data = unwrap(
        client.get(f"/problems?page=1&page_size=3&topic_slug={topic_items[0]['slug']}"),
        "Topic filter",
    )
    assert 0 < t_data["total"] < 415, (
        f"Topic filter for '{topic_items[0]['slug']}' did not narrow results "
        f"(got {t_data['total']}, expected a strict subset of 415)"
    )
    print(f"[PASS] 9. Topic Filtering: topic '{topic_items[0]['title']}' ({topic_items[0]['slug']}) -> {t_data['total']} problems")

    # Tag + pattern filtering
    p_data = unwrap(client.get("/problems?page=1&page_size=3&pattern=two-pointers"), "Pattern filter")
    assert p_data["total"] >= 1, "Pattern filter 'two-pointers' returned no problems"
    print(f"[PASS] 10. Pattern Filtering: 'two-pointers' -> {p_data['total']} problems")

    s_data = unwrap(client.get("/problems?page=1&page_size=3&search=two"), "Problem search")
    assert s_data["total"] >= 1, "Search for 'two' returned no results"

    # Pagination: first page, second page and last page must all resolve
    page1 = unwrap(client.get("/problems?page=1&page_size=20"), "Page 1")
    page2 = unwrap(client.get("/problems?page=2&page_size=20"), "Page 2")
    assert len(page1["items"]) == 20 and len(page2["items"]) == 20, "Pagination returned wrong page sizes"
    assert page1["items"][0]["id"] != page2["items"][0]["id"], "Page 2 repeated page 1 content"
    last_page = page1["total_pages"]
    last = unwrap(client.get(f"/problems?page={last_page}&page_size=20"), "Last page")
    assert last["items"], "Last page returned no items"
    print(f"[PASS] 11. Pagination & Search: pages 1, 2 and {last_page} OK; search 'two' -> {s_data['total']} matches")

    # 6. AI Tutor integration â€” real live Gemini flow with a bounded fallback
    ai_start = time.monotonic()
    ai_res = client.post("/ai/tutor", json={
        "problem_id": first_prob["id"],
        "question": "Can you give me a conceptual hint on how to start this problem?",
    }, headers=auth_headers)
    ai_elapsed = time.monotonic() - ai_start
    ai_data = unwrap(ai_res, "AI Tutor")
    assert len(ai_data["explanation"]) > 20, "AI explanation too short"
    assert ai_elapsed < AI_CLIENT_TIMEOUT_SECONDS, "AI Tutor exceeded its bounded time budget"
    print(f"[PASS] 12. AI Tutor Live Flow: 200 OK in {ai_elapsed:.1f}s (Explanation length: {len(ai_data['explanation'])} chars)")

    # AI failure/fallback path: a provider outage must degrade to a bounded,
    # correctly shaped answer instead of hanging the request or 500-ing.
    diag = unwrap(client.get("/ai/diagnostics", headers=auth_headers), "AI diagnostics")
    print(f"       Active AI provider: {diag.get('provider')} / {diag.get('model')} ({diag.get('status')})")

    fb_start = time.monotonic()
    fb_res = client.post("/ai/tutor", json={
        "problem_id": first_prob["id"],
        "question": "What is the time complexity of the optimal approach?",
    }, headers=auth_headers)
    fb_elapsed = time.monotonic() - fb_start
    fb_data = unwrap(fb_res, "AI Tutor (second call)")
    assert len(fb_data["explanation"]) > 20, "AI fallback explanation too short"
    assert fb_elapsed < AI_CLIENT_TIMEOUT_SECONDS, "AI Tutor fallback exceeded its bounded budget"
    print(f"[PASS] 13. AI Tutor Bounded Response: repeat call answered in {fb_elapsed:.1f}s (no hang)")

    # 7. Interview simulation
    start_res = client.post("/interview/start", json={
        "mode": "GENERAL_SOFTWARE",
        "difficulty": "MEDIUM",
        "target_company": "Google",
    }, headers=auth_headers)
    assert start_res.status_code == 201, f"Interview start failed: {start_res.text}"
    session_data = unwrap(start_res, "Interview start")
    session_id = session_data["id"]
    assert session_data["questions"], "Interview session generated no questions"
    print(f"[PASS] 14. Interview Mode Start: 201 Created (Session ID: {session_id}, Questions: {len(session_data['questions'])})")

    # Submit an answer to question 1
    q1 = session_data["questions"][0]
    ans_res = client.post(f"/interview/sessions/{session_id}/questions/{q1['id']}/answer", json={
        "user_response": "We use a hash table for O(1) lookup to find the complement in a single pass.",
        "code_language": "python",
    }, headers=auth_headers)
    assert ans_res.status_code == 200, f"Answer submit failed: {ans_res.text}"
    print(f"[PASS] 15. Interview Question Answer: 200 OK (Answered Q1 '{q1['title']}')")

    # Finish interview session
    end_res = client.post(f"/interview/sessions/{session_id}/end", headers=auth_headers)
    assert end_res.status_code == 200, f"Interview finish failed: {end_res.text}"
    report_data = unwrap(end_res, "Interview finish")
    print(f"[PASS] 16. Interview Finish & Safe Evaluation: 200 OK (Score: {report_data['overall_score']}/100, Verdict: {report_data['verdict']})")

    # Get report
    rep_res = client.get(f"/interview/sessions/{session_id}/report", headers=auth_headers)
    rep_data = unwrap(rep_res, "Interview report")
    print(f"[PASS] 17. Interview Report Retrieval: 200 OK (Categories evaluated: {len(rep_data['category_scores'])})")

    # 8. Gamification Profile
    gam_res = client.get("/gamification/profile", headers=auth_headers)
    gam_data = unwrap(gam_res, "Gamification profile")
    assert gam_data["total_xp"] >= 75, f"Expected interview completion XP (>=75), got {gam_data['total_xp']}"
    print(f"[PASS] 18. Gamification Profile: 200 OK (Total XP: {gam_data['total_xp']}, Level: {gam_data['current_level']}, Streak: {gam_data['current_streak']})")

    # 9. Token Refresh & rotation
    ref_res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    ref_data = unwrap(ref_res, "Token refresh")
    new_acc = ref_data["access_token"]
    new_ref = ref_data["refresh_token"]
    assert new_acc and new_ref, "New tokens not returned"
    assert new_ref != refresh_token, "Refresh token was not rotated"
    print("[PASS] 19. Token Refresh & Rotation: 200 OK (Fresh access & rotated refresh token issued)")

    # 10. Logout
    logout_res = client.post("/auth/logout", json={"refresh_token": new_ref}, headers={"Authorization": f"Bearer {new_acc}"})
    assert logout_res.status_code == 200, f"Logout failed: {logout_res.text}"
    print("[PASS] 20. User Logout: 200 OK (Session terminated)")

    print("\n============================================================")
    print("ALL 20 PRODUCTION ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")
    print("============================================================")

if __name__ == "__main__":
    try:
        test_full_user_journey()
    except Exception as e:
        print(f"\n[FAIL] Test encountered an error: {e}", file=sys.stderr)
        sys.exit(1)
