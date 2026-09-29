"""Test suite for Daily Challenge selection, completion validation, and reward claiming."""

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
from backend.app.models.progress import ProblemProgressStatus, UserProblemProgress
from backend.app.models.user import User, UserRole
from backend.app.core.security import create_access_token
from backend.app.services.gamification.daily_challenge_service import DailyChallengeService
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService


@pytest.fixture
async def daily_test_data(db_session: AsyncSession):
    """Seeds user and published problem for daily challenge."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"daily_student_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)

    problem = Problem(
        slug=f"daily-problem-{uid}",
        title="Invert Binary Tree",
        statement="Invert a binary tree recursively",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    db_session.add(problem)
    await db_session.commit()
    return {"user": user, "problem": problem}


@pytest.mark.asyncio
async def test_deterministic_daily_challenge_creation(daily_test_data, db_session: AsyncSession):
    """Verifies that the same date yields the exact same challenge deterministically."""
    c1 = await DailyChallengeService.get_or_create_daily_challenge(db_session, "2026-09-29")
    c2 = await DailyChallengeService.get_or_create_daily_challenge(db_session, "2026-09-29")
    assert c1 is not None
    assert c2 is not None
    assert c1.id == c2.id
    assert c1.problem_id == c2.problem_id
    assert c1.challenge_date == "2026-09-29"


@pytest.mark.asyncio
async def test_daily_challenge_claim_validation_and_idempotency(daily_test_data, db_session: AsyncSession):
    """Verifies solve prerequisite, reward crediting, and duplicate claim rejection."""
    user = daily_test_data["user"]
    problem = daily_test_data["problem"]
    token = create_access_token(user.id, user.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # 1. Fetch daily challenge
        get_res = await ac.get("/api/v1/practice/daily", headers={"Authorization": f"Bearer {token}"})
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["can_claim"] is False
        assert data["solved"] is False

        # 2. Attempt to claim before solving -> Must fail!
        claim_fail = await ac.post("/api/v1/practice/daily/claim", headers={"Authorization": f"Bearer {token}"})
        assert claim_fail.status_code == 400
        assert "solve the problem first" in claim_fail.text.lower()

        # 3. Simulate solving problem in UserProblemProgress
        challenge = await DailyChallengeService.get_or_create_daily_challenge(db_session, data["challenge_date"])
        prog = UserProblemProgress(
            user_id=user.id,
            problem_id=challenge.problem_id,
            status=ProblemProgressStatus.SOLVED,
            attempts_count=1,  # First attempt solve!
            successful_attempts=1,
        )
        db_session.add(prog)
        await db_session.commit()

        # 4. Claim reward -> Succeeded!
        claim_success = await ac.post("/api/v1/practice/daily/claim", headers={"Authorization": f"Bearer {token}"})
        assert claim_success.status_code == 200
        claim_data = claim_success.json()
        assert claim_data["success"] is True
        assert claim_data["xp_awarded"] == 75  # 50 base + 25 first attempt bonus

        # Check user profile XP and streak (75 daily + 75 FIRST_SOLVE achievement = 150)
        profile = await XPService.get_or_create_profile(db_session, user.id)
        assert profile.total_xp == 150
        assert profile.current_streak == 1

        # 5. Attempt duplicate claim on same date -> Must be rejected!
        claim_dup = await ac.post("/api/v1/practice/daily/claim", headers={"Authorization": f"Bearer {token}"})
        assert claim_dup.status_code == 400
        assert "already been claimed" in claim_dup.text.lower()
        # XP must NOT increase
        profile_after = await XPService.get_or_create_profile(db_session, user.id)
        assert profile_after.total_xp == 150
