"""Daily Challenge Service.

Provides deterministic problem selection per calendar date from published content,
timezone-aware day boundaries, completion verification, and idempotent reward claiming.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.content import ContentAccessLevel, ContentStatus, Problem
from backend.app.models.gamification import DailyChallenge, UserDailyChallenge
from backend.app.models.progress import ProblemProgressStatus, UserProblemProgress
from backend.app.services.gamification.achievement_service import AchievementService
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService

logger = logging.getLogger(__name__)


class DailyChallengeService:
    """Manages calendar-based daily coding challenges."""

    @classmethod
    async def get_or_create_daily_challenge(
        cls,
        db: AsyncSession,
        date_str: Optional[str] = None,
    ) -> Optional[DailyChallenge]:
        """Returns or deterministically creates the daily challenge for the specified UTC date."""
        target_date = date_str or StreakService.get_today_str()

        # Check existing
        stmt = select(DailyChallenge).where(DailyChallenge.challenge_date == target_date)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        # Deterministically select a published, free problem
        prob_stmt = (
            select(Problem)
            .where(
                Problem.status == ContentStatus.PUBLISHED,
                Problem.access_level == ContentAccessLevel.FREE,
            )
            .order_by(Problem.id)
        )
        problems = (await db.execute(prob_stmt)).scalars().all()

        if not problems:
            # Fallback to any published problem
            fallback_stmt = select(Problem).where(Problem.status == ContentStatus.PUBLISHED).order_by(Problem.id)
            problems = (await db.execute(fallback_stmt)).scalars().all()

        if not problems:
            logger.warning(f"No published problems available for Daily Challenge on {target_date}")
            return None

        # Compute deterministic integer hash from date string
        hash_digest = hashlib.sha256(target_date.encode("utf-8")).hexdigest()
        hash_val = int(hash_digest[:8], 16)
        selected_problem = problems[hash_val % len(problems)]

        challenge = DailyChallenge(
            challenge_date=target_date,
            problem_id=selected_problem.id,
            xp_reward=50,
            bonus_xp=25,
        )
        db.add(challenge)
        await db.flush()
        logger.info(f"Initialized Daily Challenge for {target_date} with Problem {selected_problem.title} ({selected_problem.slug})")

        return challenge

    @classmethod
    async def get_user_challenge_status(
        cls,
        db: AsyncSession,
        user_id: str,
        challenge: DailyChallenge,
    ) -> Optional[UserDailyChallenge]:
        """Retrieves user participation status for a daily challenge."""
        stmt = select(UserDailyChallenge).where(
            UserDailyChallenge.user_id == user_id,
            UserDailyChallenge.challenge_date == challenge.challenge_date,
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    @classmethod
    async def claim_daily_challenge_reward(
        cls,
        db: AsyncSession,
        user_id: str,
        date_str: Optional[str] = None,
    ) -> Tuple[bool, int, str]:
        """Verifies solution and credits XP reward idempotently.
        
        Returns:
            Tuple[success, xp_awarded, message]
        """
        challenge = await cls.get_or_create_daily_challenge(db, date_str)
        if not challenge:
            return False, 0, "No daily challenge found for date."

        target_date = challenge.challenge_date

        # 1. Verify user has actually solved the target problem in UserProblemProgress
        prog_stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.problem_id == challenge.problem_id,
        )
        user_progress = (await db.execute(prog_stmt)).scalar_one_or_none()

        if not user_progress or user_progress.status != ProblemProgressStatus.SOLVED:
            return False, 0, "You must solve the problem first before claiming the Daily Challenge reward."

        # 2. Check user challenge participation record
        user_challenge = await cls.get_user_challenge_status(db, user_id, challenge)
        if user_challenge and user_challenge.solved:
            return False, 0, "Daily Challenge reward has already been claimed for this date."

        first_attempt = user_progress.attempts_count == 1
        base_xp = challenge.xp_reward
        bonus_xp = challenge.bonus_xp if first_attempt else 0
        total_xp = base_xp + bonus_xp

        now = datetime.now(timezone.utc)

        if not user_challenge:
            user_challenge = UserDailyChallenge(
                user_id=user_id,
                daily_challenge_id=challenge.id,
                challenge_date=target_date,
                status="COMPLETED",
                attempts_count=user_progress.attempts_count,
                solved=True,
                first_attempt_solve=first_attempt,
                xp_awarded=total_xp,
                completed_at=now,
            )
            db.add(user_challenge)
        else:
            user_challenge.status = "COMPLETED"
            user_challenge.solved = True
            user_challenge.first_attempt_solve = first_attempt
            user_challenge.xp_awarded = total_xp
            user_challenge.completed_at = now

        await db.flush()

        # 3. Credit XP via immutable ledger idempotently
        await XPService.record_xp_event(
            db=db,
            user_id=user_id,
            event_type="DAILY_CHALLENGE",
            source_id=f"daily:{target_date}",
            amount=total_xp,
            metadata={"date": target_date, "first_attempt": first_attempt},
        )

        # 4. Advance streak
        await StreakService.record_qualifying_activity(
            db=db,
            user_id=user_id,
            activity_type="DAILY_CHALLENGE",
            now=now,
        )

        # 5. Evaluate achievements
        await AchievementService.evaluate_achievements(db, user_id)

        msg = f"Daily Challenge completed! +{total_xp} XP awarded."
        if first_attempt:
            msg += " (Includes first-attempt solve bonus!)"

        return True, total_xp, msg
