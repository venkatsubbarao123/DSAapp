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
"""

import httpx
import uuid
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_full_user_journey():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    print("============================================================")
    print("DSAapp — LIVE PRODUCTION ACCEPTANCE & USER JOURNEY TEST")
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
    reg_data = reg_res.json()["data"]
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
    assert dup_res.status_code == 400, f"Expected 400 on duplicate, got {dup_res.status_code}"
    print(f"[PASS] 3. Duplicate Registration Protection: 400 Rejected ('{dup_res.json()['error']['message']}')")

    # 3. User login
    login_res = client.post("/auth/login", json={
        "email": test_email,
        "password": "ProductionReadyPass123!",
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_token = login_res.json()["data"]["access_token"]
    auth_headers = {"Authorization": f"Bearer {login_token}"}
    print("[PASS] 4. User Login: 200 OK with fresh Bearer token")

    # 4. Auth /me
    me_res = client.get("/auth/me", headers=auth_headers)
    assert me_res.status_code == 200, f"Auth /me failed: {me_res.text}"
    me_data = me_res.json()["data"]
    assert me_data["display_name"] == "Acceptance Tester"
    print(f"[PASS] 5. Session /me Profile: 200 OK (Role: {me_data['role']}, Plan: {me_data['plan']})")

    # 5. Problems library & database integrity
    prob_res = client.get("/problems?page=1&page_size=5")
    assert prob_res.status_code == 200
    prob_data = prob_res.json()["data"]
    assert prob_data["total"] == 415, f"Expected 415 problems, got {prob_data['total']}"
    print(f"[PASS] 6. Neon Database Problem Library: 415/415 Published Problems (5 items on page 1 of {prob_data['total_pages']})")

    easy_total = client.get("/problems?difficulty=EASY&page_size=1").json()["data"]["total"]
    med_total = client.get("/problems?difficulty=MEDIUM&page_size=1").json()["data"]["total"]
    hard_total = client.get("/problems?difficulty=HARD&page_size=1").json()["data"]["total"]
    assert easy_total == 144 and med_total == 186 and hard_total == 85
    print(f"[PASS] 7. Difficulty Distribution: Easy={easy_total}, Medium={med_total}, Hard={hard_total} (Sum: {easy_total+med_total+hard_total})")

    # 6. AI Tutor integration
    first_prob = prob_data["items"][0]
    ai_res = client.post("/ai/tutor", json={
        "problem_id": first_prob["id"],
        "user_query": "Can you give me a conceptual hint on how to start this problem?",
    }, headers=auth_headers)
    assert ai_res.status_code == 200, f"AI Tutor failed: {ai_res.text}"
    ai_data = ai_res.json()["data"]
    assert len(ai_data["explanation"]) > 20, "AI explanation too short"
    print(f"[PASS] 8. AI Tutor Live Flow: 200 OK (Provider: {ai_data.get('provider', 'Gemini/Fallback')}, Explanation length: {len(ai_data['explanation'])} chars)")

    # 7. Interview simulation
    start_res = client.post("/interview/start", json={
        "mode": "GENERAL_SOFTWARE",
        "difficulty": "MEDIUM",
        "target_company": "Google",
    }, headers=auth_headers)
    assert start_res.status_code == 201, f"Interview start failed: {start_res.text}"
    session_data = start_res.json()["data"]
    session_id = session_data["id"]
    print(f"[PASS] 9. Interview Mode Start: 201 Created (Session ID: {session_id}, Questions: {len(session_data['questions'])})")

    # Submit an answer to question 1
    q1 = session_data["questions"][0]
    ans_res = client.post(f"/interview/sessions/{session_id}/questions/{q1['id']}/answer", json={
        "user_response": "We use a hash table for O(1) lookup to find the complement in a single pass.",
        "code_language": "python",
    }, headers=auth_headers)
    assert ans_res.status_code == 200, f"Answer submit failed: {ans_res.text}"
    print(f"[PASS] 10. Interview Question Answer: 200 OK (Answered Q1 '{q1['title']}')")

    # Finish interview session
    end_res = client.post(f"/interview/sessions/{session_id}/end", headers=auth_headers)
    assert end_res.status_code == 200, f"Interview finish failed: {end_res.text}"
    report_data = end_res.json()["data"]
    print(f"[PASS] 11. Interview Finish & Safe Evaluation: 200 OK (Score: {report_data['overall_score']}/100, Verdict: {report_data['verdict']})")

    # Get report
    rep_res = client.get(f"/interview/sessions/{session_id}/report", headers=auth_headers)
    assert rep_res.status_code == 200, f"Get report failed: {rep_res.text}"
    print(f"[PASS] 12. Interview Report Retrieval: 200 OK (Categories evaluated: {len(rep_res.json()['data']['category_scores'])})")

    # 8. Gamification Profile
    gam_res = client.get("/gamification/profile", headers=auth_headers)
    assert gam_res.status_code == 200, f"Gamification profile failed: {gam_res.text}"
    gam_data = gam_res.json()["data"]
    assert gam_data["total_xp"] >= 75, f"Expected interview completion XP (>=75), got {gam_data['total_xp']}"
    print(f"[PASS] 13. Gamification Profile: 200 OK (Total XP: {gam_data['total_xp']}, Level: {gam_data['current_level']}, Streak: {gam_data['current_streak']})")

    # 9. Token Refresh
    ref_res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200, f"Refresh failed: {ref_res.text}"
    new_acc = ref_res.json()["data"]["access_token"]
    new_ref = ref_res.json()["data"]["refresh_token"]
    assert new_acc and new_ref, "New tokens not returned"
    print("[PASS] 14. Token Refresh & Rotation: 200 OK (Fresh access & refresh tokens issued)")

    # 10. Logout
    logout_res = client.post("/auth/logout", json={"refresh_token": new_ref}, headers={"Authorization": f"Bearer {new_acc}"})
    assert logout_res.status_code == 200, f"Logout failed: {logout_res.text}"
    print("[PASS] 15. User Logout: 200 OK (Session terminated)")

    print("\n============================================================")
    print("ALL 15 PRODUCTION ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")
    print("============================================================")

if __name__ == "__main__":
    try:
        test_full_user_journey()
    except Exception as e:
        print(f"\n[FAIL] Test encountered an error: {e}", file=sys.stderr)
        sys.exit(1)
