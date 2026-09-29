"""Streak calculation and maintenance service.

Tracks consecutive daily learning activities with timezone-safe UTC day boundaries,
streak freeze protections, idempotent same-day activities, and milestone XP rewards.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.gamification import UserGamificationProfile
from backend.app.services.gamification.xp_service import XPService

logger = logging.getLogger(__name__)


class StreakService:
    """Manages learner daily activity streaks and freezes."""

    @staticmethod
    def get_today_str(now: Optional[datetime] = None) -> str:
        """Returns today's date string in YYYY-MM-DD (UTC)."""
        dt = now or datetime.now(timezone.utc)
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def get_yesterday_str(now: Optional[datetime] = None) -> str:
        """Returns yesterday's date string in YYYY-MM-DD (UTC)."""
        dt = now or datetime.now(timezone.utc)
        return (dt - timedelta(days=1)).strftime("%Y-%m-%d")

    @staticmethod
    def get_day_before_yesterday_str(now: Optional[datetime] = None) -> str:
        """Returns date string for two days ago (UTC)."""
        dt = now or datetime.now(timezone.utc)
        return (dt - timedelta(days=2)).strftime("%Y-%m-%d")

    @classmethod
    async def record_qualifying_activity(
        cls,
        db: AsyncSession,
        user_id: str,
        activity_type: str,
        now: Optional[datetime] = None,
    ) -> Tuple[int, int, bool]:
        """Records a qualifying learning activity (solve, daily challenge, revision).
        
        Returns:
            Tuple[current_streak, longest_streak, is_streak_incremented]
        """
        profile = await XPService.get_or_create_profile(db, user_id)
        today = cls.get_today_str(now)
        yesterday = cls.get_yesterday_str(now)
        two_days_ago = cls.get_day_before_yesterday_str(now)

        last_date = profile.last_activity_date

        if last_date == today:
            # Already maintained for today, idempotent
            return profile.current_streak, profile.longest_streak, False

        incremented = True
        if last_date is None:
            # First recorded qualifying activity
            profile.current_streak = 1
        elif last_date == yesterday:
            # Consecutive day!
            profile.current_streak += 1
        elif last_date == two_days_ago and profile.streak_freeze_count > 0:
            # Used streak freeze to preserve yesterday's missed day
            profile.streak_freeze_count -= 1
            profile.current_streak += 1
            logger.info(f"User {user_id} consumed 1 streak freeze. Streak preserved at {profile.current_streak}")
        else:
            # Missed more than allowed without freeze: reset streak
            profile.current_streak = 1

        profile.longest_streak = max(profile.longest_streak, profile.current_streak)
        profile.last_activity_date = today
        await db.flush()

        # Check streak milestones
        if profile.current_streak == 7:
            await XPService.record_xp_event(
                db=db,
                user_id=user_id,
                event_type="STREAK_MILESTONE",
                source_id=f"streak:7:{today}",
                amount=70,
                metadata={"milestone": 7, "date": today},
            )
        elif profile.current_streak == 30:
            await XPService.record_xp_event(
                db=db,
                user_id=user_id,
                event_type="STREAK_MILESTONE",
                source_id=f"streak:30:{today}",
                amount=300,
                metadata={"milestone": 30, "date": today},
            )

        return profile.current_streak, profile.longest_streak, incremented
