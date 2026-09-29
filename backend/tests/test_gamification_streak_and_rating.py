"""Test suite for streak maintenance, freeze protections, and skill rating."""

import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import app
from backend.app.models.user import User, UserRole
from backend.app.core.security import create_access_token
from backend.app.services.gamification.rating_service import RatingService
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService


@pytest.mark.asyncio
async def test_streak_progression_idempotency_and_resets(db_session: AsyncSession):
    """Tests day-by-day streak transitions, same-day idempotency, and reset behavior."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"streak_tester_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    base_time = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)

    # Day 1: First activity -> Streak = 1
    curr, longest, inc = await StreakService.record_qualifying_activity(
        db=db_session, user_id=user.id, activity_type="PROBLEM_SOLVE", now=base_time
    )
    assert curr == 1
    assert longest == 1
    assert inc is True

    # Day 1 Later: Second activity same day -> Idempotent! Streak stays 1
    curr2, longest2, inc2 = await StreakService.record_qualifying_activity(
        db=db_session, user_id=user.id, activity_type="PROBLEM_SOLVE", now=base_time + timedelta(hours=4)
    )
    assert curr2 == 1
    assert longest2 == 1
    assert inc2 is False

    # Day 2: Next consecutive day -> Streak = 2
    day2_time = base_time + timedelta(days=1)
    curr3, longest3, inc3 = await StreakService.record_qualifying_activity(
        db=db_session, user_id=user.id, activity_type="PROBLEM_SOLVE", now=day2_time
    )
    assert curr3 == 2
    assert longest3 == 2
    assert inc3 is True

    # Day 4: Missed Day 3 without freeze -> Streak resets to 1
    day4_time = base_time + timedelta(days=3)
    curr4, longest4, inc4 = await StreakService.record_qualifying_activity(
        db=db_session, user_id=user.id, activity_type="PROBLEM_SOLVE", now=day4_time
    )
    assert curr4 == 1
    assert longest4 == 2  # Longest streak preserved!


@pytest.mark.asyncio
async def test_streak_freeze_consumption(db_session: AsyncSession):
    """Verifies that streak freeze protects streak over 1 missed day."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"freeze_tester_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    profile = await XPService.get_or_create_profile(db_session, user.id)
    profile.streak_freeze_count = 1
    await db_session.commit()

    base_time = datetime(2026, 9, 20, 10, 0, 0, tzinfo=timezone.utc)

    # Day 1: Streak = 1
    await StreakService.record_qualifying_activity(
        db=db_session, user_id=user.id, activity_type="PROBLEM_SOLVE", now=base_time
    )

    # Day 3: Skipped Day 2, but has 1 streak freeze!
    day3_time = base_time + timedelta(days=2)
    curr, longest, _ = await StreakService.record_qualifying_activity(
        db=db_session, user_id=user.id, activity_type="PROBLEM_SOLVE", now=day3_time
    )
    # Streak should continue to 2 and freeze count should be 0
    assert curr == 2
    assert longest == 2

    profile_after = await XPService.get_or_create_profile(db_session, user.id)
    assert profile_after.streak_freeze_count == 0


@pytest.mark.asyncio
async def test_rating_service_and_audit_history(db_session: AsyncSession):
    """Verifies skill rating progression and transparent history logs."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"rating_tester_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Initial rating is 1000
    r1 = await RatingService.record_problem_solve(
        db=db_session, user_id=user.id, problem_id="prob_easy_1", difficulty="EASY"
    )
    assert r1 == 1005  # +5

    r2 = await RatingService.record_problem_solve(
        db=db_session, user_id=user.id, problem_id="prob_med_1", difficulty="MEDIUM"
    )
    assert r2 == 1017  # +12

    r3 = await RatingService.record_problem_solve(
        db=db_session, user_id=user.id, problem_id="prob_hard_1", difficulty="HARD"
    )
    assert r3 == 1042  # +25

    # Session completion with 100% accuracy bonus (+10)
    r4 = await RatingService.record_session_completion(
        db=db_session, user_id=user.id, session_id="sess_123", accuracy=1.0
    )
    assert r4 == 1052  # +10

    await db_session.commit()

    token = create_access_token(user.id, user.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        rating_res = await ac.get(
            "/api/v1/gamification/rating",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert rating_res.status_code == 200
        data = rating_res.json()
        assert data["current_rating"] == 1052
        assert len(data["history"]) == 4
        assert data["history"][0]["new_rating"] == 1052
        assert data["history"][0]["reason"] == "High accuracy session completion (>=80%)"
