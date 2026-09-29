"""Test suite for XP accounting, level progression, and ledger idempotency."""

import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import app
from backend.app.models.user import User, UserRole
from backend.app.core.security import create_access_token
from backend.app.services.gamification.level_service import LevelService
from backend.app.services.gamification.xp_service import XPService


def test_level_service_deterministic_calculations():
    """Validates exact mathematical level curves without floating point errors."""
    assert LevelService.calculate_level(0) == 1
    assert LevelService.calculate_level(50) == 1
    assert LevelService.calculate_level(99) == 1
    assert LevelService.calculate_level(100) == 2
    assert LevelService.calculate_level(299) == 2
    assert LevelService.calculate_level(300) == 3
    assert LevelService.calculate_level(599) == 3
    assert LevelService.calculate_level(600) == 4
    assert LevelService.calculate_level(999) == 4
    assert LevelService.calculate_level(1000) == 5

    # Check progress percentage
    prog = LevelService.calculate_progress(50)
    assert prog.current_level == 1
    assert prog.level_floor_xp == 0
    assert prog.level_ceiling_xp == 100
    assert prog.xp_in_current_level == 50
    assert prog.xp_needed_for_next_level == 50
    assert prog.progress_percent == 50.0

    prog2 = LevelService.calculate_progress(200)
    assert prog2.current_level == 2
    assert prog2.level_floor_xp == 100
    assert prog2.level_ceiling_xp == 300
    assert prog2.xp_in_current_level == 100
    assert prog2.xp_needed_for_next_level == 100
    assert prog2.progress_percent == 50.0


@pytest.mark.asyncio
async def test_xp_ledger_and_idempotency_prevents_duplicate_rewards(db_session: AsyncSession):
    """Verifies atomic ledger entries and idempotency preventing duplicate XP."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"xp_student_{uid}@example.com",
        hashed_password="hashed_pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # 1. First award
    tx1, is_new1, level1 = await XPService.record_xp_event(
        db=db_session,
        user_id=user.id,
        event_type="PROBLEM_SOLVE",
        source_id="prob_test_123",
        amount=50,
    )
    assert is_new1 is True
    assert tx1 is not None
    assert tx1.amount == 50

    profile = await XPService.get_or_create_profile(db_session, user.id)
    assert profile.total_xp == 50
    assert profile.current_level == 1

    # 2. Duplicate award attempt with same source_id
    tx2, is_new2, level2 = await XPService.record_xp_event(
        db=db_session,
        user_id=user.id,
        event_type="PROBLEM_SOLVE",
        source_id="prob_test_123",
        amount=50,
    )
    assert is_new2 is False
    # Total XP must remain 50, NOT 100
    profile_reloaded = await XPService.get_or_create_profile(db_session, user.id)
    assert profile_reloaded.total_xp == 50

    # 3. Third award crossing level boundary to Level 2 (50 + 60 = 110 XP)
    tx3, is_new3, level3 = await XPService.record_xp_event(
        db=db_session,
        user_id=user.id,
        event_type="PROBLEM_SOLVE",
        source_id="prob_test_456",
        amount=60,
    )
    assert is_new3 is True
    assert level3 == 2

    profile_final = await XPService.get_or_create_profile(db_session, user.id)
    assert profile_final.total_xp == 110
    assert profile_final.current_level == 2


@pytest.mark.asyncio
async def test_gamification_profile_and_ledger_endpoints(db_session: AsyncSession):
    """Verifies GET /gamification/profile and /gamification/xp API endpoints."""
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"profile_student_{uid}@example.com",
        hashed_password="hashed_pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(user.id, user.role.value)

    # Award 100 XP
    await XPService.record_xp_event(
        db=db_session,
        user_id=user.id,
        event_type="DAILY_CHALLENGE",
        source_id="daily_2026-09-29",
        amount=100,
    )
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        prof_res = await ac.get(
            "/api/v1/gamification/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert prof_res.status_code == 200
        prof_data = prof_res.json()
        assert prof_data["total_xp"] == 100
        assert prof_data["current_level"] == 2

        xp_res = await ac.get(
            "/api/v1/gamification/xp",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert xp_res.status_code == 200
        xp_data = xp_res.json()
        assert xp_data["total_count"] == 1
        assert xp_data["transactions"][0]["amount"] == 100
        assert xp_data["transactions"][0]["event_type"] == "DAILY_CHALLENGE"

        # Security check: Arbitrary client POST to /xp must not be allowed
        spoof_res = await ac.post(
            "/api/v1/gamification/xp",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": 999999},
        )
        assert spoof_res.status_code in (404, 405)  # Method Not Allowed or Not Found
