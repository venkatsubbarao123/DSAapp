"""Practice Rating and Skill Progression Service.

Calculates server-authoritative practice ratings based on problem difficulty
and session performance with full historical auditing.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.content import ProblemDifficulty
from backend.app.models.gamification import RatingHistory
from backend.app.services.gamification.xp_service import XPService

logger = logging.getLogger(__name__)

RATING_DELTA_BY_DIFFICULTY = {
    ProblemDifficulty.EASY.value: 5,
    ProblemDifficulty.MEDIUM.value: 12,
    ProblemDifficulty.HARD.value: 25,
    ProblemDifficulty.EXPERT.value: 40,
}


class RatingService:
    """Manages skill rating calculations and audit logging."""

    @classmethod
    async def adjust_rating(
        cls,
        db: AsyncSession,
        user_id: str,
        delta: int,
        reason: str,
        source_id: str | None = None,
    ) -> int:
        """Applies a rating delta and logs the transaction in RatingHistory.

        Returns:
            The new rating value.
        """
        profile = await XPService.get_or_create_profile(db, user_id)
        prev_rating = profile.current_rating
        new_rating = max(100, prev_rating + delta)  # Floor rating at 100

        profile.current_rating = new_rating
        await db.flush()

        history = RatingHistory(
            user_id=user_id,
            previous_rating=prev_rating,
            new_rating=new_rating,
            change=delta,
            reason=reason,
            source_id=source_id,
        )
        db.add(history)
        await db.flush()

        logger.info(
            f"User {user_id} rating adjusted: {prev_rating} -> {new_rating} ({'+' if delta >= 0 else ''}{delta}) [{reason}]"
        )
        return new_rating

    @classmethod
    async def record_problem_solve(
        cls,
        db: AsyncSession,
        user_id: str,
        problem_id: str,
        difficulty: str,
    ) -> int:
        """Awards rating points for a successful problem solve."""
        delta = RATING_DELTA_BY_DIFFICULTY.get(difficulty.upper(), 8)
        return await cls.adjust_rating(
            db=db,
            user_id=user_id,
            delta=delta,
            reason=f"Problem solve ({difficulty.upper()})",
            source_id=problem_id,
        )

    @classmethod
    async def record_session_completion(
        cls,
        db: AsyncSession,
        user_id: str,
        session_id: str,
        accuracy: float,
    ) -> int | None:
        """Awards bonus rating for high-accuracy session completion."""
        if accuracy >= 0.8:
            return await cls.adjust_rating(
                db=db,
                user_id=user_id,
                delta=10,
                reason="High accuracy session completion (>=80%)",
                source_id=session_id,
            )
        return None
