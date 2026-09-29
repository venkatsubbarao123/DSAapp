"""Test suite for Achievements catalog/unlocks and Leaderboard ranking calculations."""

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
from backend.app.models.user import User, UserProfile, UserRole
from backend.app.core.security import create_access_token
from backend.app.services.gamification.achievement_service import AchievementService
from backend.app.services.gamification.leaderboard_service import LeaderboardService
from backend.app.services.gamification.xp_service import XPService


@pytest.fixture
async def achievement_test_data(db_session: AsyncSession):
    """Seeds two users with different scores for achievement and leaderboard testing."""
    uid = uuid.uuid4().hex[:6]
    user1 = User(
        email=f"leader_alpha_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    user2 = User(
        email=f"leader_beta_{uid}@example.com",
        hashed_password="pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([user1, user2])
    await db_session.flush()

    prof1 = UserProfile(user_id=user1.id, display_name=f"AlphaCoder_{uid}")
    prof2 = UserProfile(user_id=user2.id, display_name=f"BetaSolver_{uid}")
    db_session.add_all([prof1, prof2])

    problem = Problem(
        slug=f"achieve-prob-{uid}",
        title="Two Sum Achievement Target",
        statement="Find pair adding to target",
        difficulty=ProblemDifficulty.EASY,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    db_session.add(problem)
    await db_session.commit()
    return {"user1": user1, "user2": user2, "problem": problem, "p1_name": prof1.display_name, "p2_name": prof2.display_name}


@pytest.mark.asyncio
async def test_achievements_catalog_and_idempotent_evaluation(achievement_test_data, db_session: AsyncSession):
    """Verifies achievement catalog seeding, progress criteria evaluation, and idempotent unlock."""
    user1 = achievement_test_data["user1"]
    problem = achievement_test_data["problem"]
    token = create_access_token(user1.id, user1.role.value)

    # 1. Fetch initial catalog
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        res = await ac.get("/api/v1/gamification/achievements", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["total_achievements"] == 12
        assert data["unlocked_count"] == 0

        # 2. Simulate User 1 solving their first problem
        prog = UserProblemProgress(
            user_id=user1.id,
            problem_id=problem.id,
            status=ProblemProgressStatus.SOLVED,
            attempts_count=1,
            successful_attempts=1,
        )
        db_session.add(prog)
        await db_session.commit()

        # 3. Evaluate achievements
        unlocked = await AchievementService.evaluate_achievements(db_session, user1.id)
        assert len(unlocked) >= 1
        assert any(ach.code == "FIRST_SOLVE" for ach, _ in unlocked)

        # 4. Check achievements endpoint again
        res2 = await ac.get("/api/v1/gamification/achievements", headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["unlocked_count"] >= 1
        first_solve_badge = next(a for a in data2["achievements"] if a["code"] == "FIRST_SOLVE")
        assert first_solve_badge["unlocked"] is True

        # 5. Evaluate again: must be idempotent!
        unlocked_again = await AchievementService.evaluate_achievements(db_session, user1.id)
        assert len(unlocked_again) == 0


@pytest.mark.asyncio
async def test_leaderboard_rankings_and_privacy_safe_names(achievement_test_data, db_session: AsyncSession):
    """Verifies deterministic ranking order, privacy-safe handles, and current user lookup."""
    user1 = achievement_test_data["user1"]
    user2 = achievement_test_data["user2"]
    p1_name = achievement_test_data["p1_name"]
    p2_name = achievement_test_data["p2_name"]

    # Credit User 1 with 200 XP and streak 5
    p1 = await XPService.get_or_create_profile(db_session, user1.id)
    p1.total_xp = 200
    p1.current_streak = 5

    # Credit User 2 with 500 XP and streak 2
    p2 = await XPService.get_or_create_profile(db_session, user2.id)
    p2.total_xp = 500
    p2.current_streak = 2
    await db_session.commit()

    token1 = create_access_token(user1.id, user1.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # All time XP leaderboard
        res = await ac.get(
            "/api/v1/leaderboards?category=all_time_xp&limit=10&offset=0",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["entries"]) >= 2
        # Verify order: user with 500 XP ranks higher than user with 200 XP
        entry_scores = [e["score"] for e in data["entries"]]
        assert entry_scores == sorted(entry_scores, reverse=True)
        
        # Ensure email is NEVER exposed
        assert user1.email not in str(data)
        assert user2.email not in str(data)

        # Current user rank endpoint
        me_res = await ac.get("/api/v1/leaderboards/me", headers={"Authorization": f"Bearer {token1}"})
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["all_time_xp"]["score"] == 200
        assert me_data["all_time_xp"]["display_name"] == p1_name
