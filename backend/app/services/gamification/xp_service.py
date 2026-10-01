"""XP Transaction and Ledger Service.

Server-authoritative XP accounting ensuring:
- Immutable transactional ledger (XPTransaction)
- Idempotency guarantees preventing duplicate rewards
- Authoritative balance and level updates on UserGamificationProfile
"""

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.gamification import (
    UserGamificationProfile,
    XPTransaction,
)
from backend.app.services.gamification.level_service import LevelService

logger = logging.getLogger(__name__)

# Standard authoritative reward amounts
XP_REWARDS = {
    "PROBLEM_SOLVE_EASY": 20,
    "PROBLEM_SOLVE_MEDIUM": 40,
    "PROBLEM_SOLVE_HARD": 75,
    "PROBLEM_SOLVE_EXPERT": 120,
    "DAILY_CHALLENGE": 50,
    "DAILY_CHALLENGE_FIRST_ATTEMPT_BONUS": 25,
    "PRACTICE_SESSION_COMPLETE": 30,
    "REVISION_COMPLETE": 15,
    "STREAK_MILESTONE_7": 70,
    "STREAK_MILESTONE_30": 300,
}


class XPService:
    """Manages XP rewards, ledgers, and profile balance updates."""

    @staticmethod
    async def get_or_create_profile(
        db: AsyncSession, user_id: str
    ) -> UserGamificationProfile:
        """Retrieves or initializes the authoritative gamification profile for a user."""
        stmt = select(UserGamificationProfile).where(
            UserGamificationProfile.user_id == user_id
        )
        result = await db.execute(stmt)
        profile: UserGamificationProfile | None = result.scalar_one_or_none()

        if not profile:
            profile = UserGamificationProfile(
                user_id=user_id,
                total_xp=0,
                current_level=1,
                current_streak=0,
                longest_streak=0,
                last_activity_date=None,
                streak_freeze_count=0,
                current_rating=1000,
                total_solves=0,
            )
            db.add(profile)
            await db.flush()

        return profile

    @classmethod
    async def record_xp_event(
        cls,
        db: AsyncSession,
        user_id: str,
        event_type: str,
        source_id: str,
        amount: int,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[XPTransaction | None, bool, int]:
        """Atomically records an XP event in the ledger if not already granted.

        Returns:
            Tuple[transaction_or_none, is_new_reward, new_level]
        """
        if amount <= 0:
            return None, False, 1

        idempotency_key = f"{user_id}:{event_type}:{source_id}"

        # Check existing transaction
        check_stmt = select(XPTransaction).where(
            XPTransaction.idempotency_key == idempotency_key
        )
        existing: XPTransaction | None = (await db.execute(check_stmt)).scalar_one_or_none()
        if existing:
            # Already awarded, do not double-count
            profile = await cls.get_or_create_profile(db, user_id)
            return existing, False, profile.current_level

        # Create new ledger entry
        metadata_str = json.dumps(metadata) if metadata else None
        tx = XPTransaction(
            user_id=user_id,
            event_type=event_type,
            source_id=source_id,
            idempotency_key=idempotency_key,
            amount=amount,
            metadata_json=metadata_str,
        )

        try:
            async with db.begin_nested():
                db.add(tx)

                # Update profile
                profile = await cls.get_or_create_profile(db, user_id)
                old_level = profile.current_level
                profile.total_xp += amount

                new_level = LevelService.calculate_level(profile.total_xp)
                profile.current_level = new_level
                await db.flush()

                level_up = new_level > old_level
                if level_up:
                    logger.info(
                        f"User {user_id} leveled up from {old_level} to {new_level} (Total XP: {profile.total_xp})"
                    )

                return tx, True, new_level
        except IntegrityError:
            # Race condition / idempotency constraint: another concurrent request already recorded this XP
            logger.info(f"Duplicate XP event ignored via idempotency key: {idempotency_key}")
            existing_tx = (await db.execute(check_stmt)).scalar_one_or_none()
            profile = await cls.get_or_create_profile(db, user_id)
            return existing_tx, False, profile.current_level
