"""Security, IDOR, Anti-Cheat, and Premium Gate test suite for Phase 8."""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_access_token
from backend.app.models.contest import Contest, ContestStatus
from backend.app.models.interview import InterviewMode, InterviewSession
from backend.app.models.user import User, UserRole


@pytest.fixture
async def sec_test_users(db_session: AsyncSession):
    """Sets up two isolated users and a premium-required contest."""
    uid = uuid.uuid4().hex[:6]
    now_utc = datetime.now(timezone.utc)

    user_a = User(
        email=f"user_a_{uid}@example.com",
        hashed_password="hashed_pwd_a",
        role=UserRole.STUDENT,
        is_active=True,
    )
    user_b = User(
        email=f"user_b_{uid}@example.com",
        hashed_password="hashed_pwd_b",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    await db_session.flush()

    premium_contest = Contest(
        title=f"Pro League Contest {uid}",
        slug=f"pro-league-{uid}",
        description="Exclusive to Pro subscribers",
        status=ContestStatus.LIVE.value,
        start_at=now_utc - timedelta(minutes=10),
        end_at=now_utc + timedelta(hours=2),
        duration_seconds=7200,
        visibility="PUBLIC",
        premium_required=True,
    )
    db_session.add(premium_contest)

    # User A starts an interview
    session_a = InterviewSession(
        user_id=user_a.id,
        mode=InterviewMode.GENERAL_SOFTWARE.value,
        status="IN_PROGRESS",
        duration_seconds=2700,
        total_questions=5,
        score=0,
    )
    db_session.add(session_a)
    await db_session.commit()

    return {
        "user_a": user_a,
        "user_b": user_b,
        "premium_contest": premium_contest,
        "session_a": session_a,
    }


@pytest.mark.asyncio
async def test_interview_idor_protection(
    client: AsyncClient,
    sec_test_users: dict,
):
    """STRICT IDOR DEFENSE: User B cannot view, answer, or complete User A's interview."""
    user_b = sec_test_users["user_b"]
    session_a = sec_test_users["session_a"]

    token_b = create_access_token(user_id=user_b.id, role=user_b.role.value)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User B tries to view User A's session -> 404 Not Found (concealed)
    get_res = await client.get(f"/api/v1/interview/sessions/{session_a.id}", headers=headers_b)
    assert get_res.status_code == 404

    # 2. User B tries to answer a question in User A's session -> 400 Bad Request
    ans_res = await client.post(
        f"/api/v1/interview/sessions/{session_a.id}/answer",
        json={"question_id": str(uuid.uuid4()), "answer": "Malicious answer"},
        headers=headers_b,
    )
    assert ans_res.status_code == 400

    # 3. User B tries to finish User A's session -> 400 Bad Request
    fin_res = await client.post(
        f"/api/v1/interview/sessions/{session_a.id}/finish",
        headers=headers_b,
    )
    assert fin_res.status_code == 400

    # 4. User B tries to view User A's report -> 404 Not Found
    rep_res = await client.get(f"/api/v1/interview/sessions/{session_a.id}/report", headers=headers_b)
    assert rep_res.status_code == 404


@pytest.mark.asyncio
async def test_premium_contest_gate(
    client: AsyncClient,
    sec_test_users: dict,
):
    """Verifies that non-premium users are strictly rejected from joining premium contests."""
    user = sec_test_users["user_a"]
    contest = sec_test_users["premium_contest"]

    token = create_access_token(user_id=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # Free user attempts to join Pro contest
    join_res = await client.post(f"/api/v1/contests/{contest.slug}/join", headers=headers)
    assert join_res.status_code == 400
    assert "Pro subscription" in join_res.json().get("detail", "") or "Pro subscription" in join_res.text


@pytest.mark.asyncio
async def test_zero_client_authority_checks(
    client: AsyncClient,
    sec_test_users: dict,
):
    """Verifies that clients cannot inject scores, ratings, or timers via API parameters."""
    user = sec_test_users["user_a"]
    token = create_access_token(user_id=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. No endpoint accepts client-supplied scores for interview
    fake_score_res = await client.post(
        "/api/v1/interview/sessions",
        json={"mode": "GENERAL_SOFTWARE", "score": 100, "status": "COMPLETED"},
        headers=headers,
    )
    assert fake_score_res.status_code == 201
    created_session = fake_score_res.json()
    assert created_session["score"] == 0
    assert created_session["status"] == "IN_PROGRESS"

    # 2. No endpoint exists for client to set arbitrary CP rating
    fake_rating_res = await client.post(
        "/api/v1/competitive/profile",
        json={"current_rating": 2800},
        headers=headers,
    )
    # Method not allowed or not found
    assert fake_rating_res.status_code in (404, 405)
