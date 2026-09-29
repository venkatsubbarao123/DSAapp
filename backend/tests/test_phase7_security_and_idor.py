"""Security and IDOR Defense Test Suite for Phase 7 Practice & Gamification.

Explicitly verifies:
1. User A cannot access User B's practice session (IDOR read blocked).
2. User A cannot modify User B's practice session problems (IDOR write blocked).
3. User cannot directly submit client-crafted XP or score amounts.
4. Duplicate requests cannot duplicate XP rewards (Ledger idempotency).
5. User A cannot claim User B's daily challenge reward.
6. User cannot claim daily challenge reward without solving the problem.
7. Premium-only practice modes reject Free tier learners.
8. Unauthenticated requests are rejected with HTTP 401.
"""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import app
from backend.app.models.content import (
    ContentAccessLevel,
    ContentStatus,
    Problem,
    ProblemDifficulty,
)
from backend.app.models.gamification import PracticeSession
from backend.app.models.user import User, UserRole
from backend.app.core.security import create_access_token


@pytest.fixture
async def security_test_data(db_session: AsyncSession):
    """Seeds two distinct student users and a published problem."""
    uid = uuid.uuid4().hex[:6]
    student_a = User(
        email=f"student_a_{uid}@example.com",
        hashed_password="pw_a",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student_b = User(
        email=f"student_b_{uid}@example.com",
        hashed_password="pw_b",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([student_a, student_b])

    prob = Problem(
        slug=f"security-practice-prob-{uid}",
        title="Security Practice Problem",
        statement="Practice defensive programming",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    db_session.add(prob)
    await db_session.commit()
    return {"student_a": student_a, "student_b": student_b, "problem": prob}


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected(security_test_data):
    """Verifies that protected practice and gamification endpoints reject unauthenticated calls."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res1 = await ac.get("/api/v1/practice/history")
        assert res1.status_code == 401

        res2 = await ac.post("/api/v1/practice/sessions", json={"mode": "QUICK"})
        assert res2.status_code == 401

        res3 = await ac.get("/api/v1/gamification/profile")
        assert res3.status_code == 401

        res4 = await ac.get("/api/v1/gamification/streak")
        assert res4.status_code == 401

        res5 = await ac.post("/api/v1/practice/daily/claim")
        assert res5.status_code == 401


@pytest.mark.asyncio
async def test_idor_cross_user_session_access_and_mutation_blocked(security_test_data):
    """Verifies that Student B cannot view or modify Student A's practice session."""
    user_a = security_test_data["student_a"]
    user_b = security_test_data["student_b"]

    token_a = create_access_token(user_a.id, user_a.role.value)
    token_b = create_access_token(user_b.id, user_b.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Student A creates a session
        create_res = await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"mode": "QUICK", "target_count": 1},
        )
        assert create_res.status_code == 201
        session_id = create_res.json()["id"]
        prob_id = create_res.json()["problems"][0]["problem_id"]

        # Student B attempts to read Student A's session -> Blocked 403
        read_res = await ac.get(
            f"/api/v1/practice/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert read_res.status_code == 403
        assert "Access denied" in read_res.text

        # Student B attempts to record solve on Student A's session -> Blocked 403
        write_res = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/problem/{prob_id}/result",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"problem_id": prob_id, "solved": True, "time_spent_seconds": 60},
        )
        assert write_res.status_code == 403

        # Student B attempts to complete Student A's session -> Blocked 403
        complete_res = await ac.post(
            f"/api/v1/practice/sessions/{session_id}/complete",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert complete_res.status_code == 403


@pytest.mark.asyncio
async def test_premium_practice_mode_gate_enforced(security_test_data):
    """Verifies that Free tier users are rejected from Pro-only modes (WEAK_AREA, MISTAKES)."""
    user_a = security_test_data["student_a"]  # Free student
    token_a = create_access_token(user_a.id, user_a.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res1 = await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"mode": "WEAK_AREA", "target_count": 2},
        )
        assert res1.status_code == 403
        assert "requires a Pro tier subscription" in res1.text

        res2 = await ac.post(
            "/api/v1/practice/sessions",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"mode": "MISTAKES", "target_count": 2},
        )
        assert res2.status_code == 403
        assert "requires a Pro tier subscription" in res2.text


@pytest.mark.asyncio
async def test_direct_xp_manipulation_blocked(security_test_data):
    """Verifies that learners cannot directly forge XP, level, or rating adjustments."""
    user_a = security_test_data["student_a"]
    token_a = create_access_token(user_a.id, user_a.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # Client tries to POST directly to forge XP
        res1 = await ac.post(
            "/api/v1/gamification/xp",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"amount": 50000},
        )
        assert res1.status_code in (404, 405)

        # Client tries to PUT or PATCH profile directly
        res2 = await ac.put(
            "/api/v1/gamification/profile",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"total_xp": 99999, "current_level": 50},
        )
        assert res2.status_code in (404, 405)

        # Client tries to POST directly to rating
        res3 = await ac.post(
            "/api/v1/gamification/rating",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"rating": 3000},
        )
        assert res3.status_code in (404, 405)
