"""Adaptive Difficulty Engine.

Evaluates recent learner accuracy and performance signals to dynamically recommend
calibrated difficulty tiers (EASY, MEDIUM, HARD, EXPERT) preventing both boredom and burnout.
"""

import logging
from typing import List, Tuple
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.content import ProblemDifficulty
from backend.app.models.progress import Submission, SubmissionStatus

logger = logging.getLogger(__name__)

DIFFICULTY_LADDER = [
    ProblemDifficulty.EASY.value,
    ProblemDifficulty.MEDIUM.value,
    ProblemDifficulty.HARD.value,
    ProblemDifficulty.EXPERT.value,
]


class AdaptiveDifficultyService:
    """Calculates student dynamic difficulty calibration."""

    @classmethod
    async def determine_adaptive_difficulty(
        cls,
        db: AsyncSession,
        user_id: str,
        current_preferred: str = ProblemDifficulty.EASY.value,
    ) -> Tuple[str, str]:
        """Analyzes recent performance and returns (recommended_difficulty, rationale)."""
        # Fetch the last 5 finalized submissions
        stmt = (
            select(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.status.in_([
                    SubmissionStatus.ACCEPTED,
                    SubmissionStatus.WRONG_ANSWER,
                    SubmissionStatus.TIME_LIMIT_EXCEEDED,
                    SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
                    SubmissionStatus.RUNTIME_ERROR,
                ]),
            )
            .order_by(desc(Submission.created_at))
            .limit(5)
        )
        recent_subs = (await db.execute(stmt)).scalars().all()

        curr_diff = current_preferred.upper()
        if curr_diff not in DIFFICULTY_LADDER:
            curr_diff = ProblemDifficulty.EASY.value

        curr_idx = DIFFICULTY_LADDER.index(curr_diff)

        if len(recent_subs) < 3:
            return curr_diff, "Maintaining current difficulty level as baseline performance data is being gathered."

        # Check consecutive solves
        consecutive_solves = 0
        for sub in recent_subs:
            if sub.status == SubmissionStatus.ACCEPTED:
                consecutive_solves += 1
            else:
                break

        # Check consecutive failures
        consecutive_failures = 0
        for sub in recent_subs:
            if sub.status != SubmissionStatus.ACCEPTED:
                consecutive_failures += 1
            else:
                break

        if consecutive_solves >= 3:
            if curr_idx < len(DIFFICULTY_LADDER) - 1:
                next_diff = DIFFICULTY_LADDER[curr_idx + 1]
                return (
                    next_diff,
                    f"Strong performance with {consecutive_solves} consecutive accepted solutions! Stepping up challenge to {next_diff}."
                )
            else:
                return (
                    curr_diff,
                    f"Max difficulty ({curr_diff}) reached with {consecutive_solves} consecutive solves. Maintaining master tier challenge."
                )

        if consecutive_failures >= 3:
            if curr_idx > 0:
                prev_diff = DIFFICULTY_LADDER[curr_idx - 1]
                return (
                    prev_diff,
                    f"{consecutive_failures} consecutive challenging attempts detected. Easing difficulty to {prev_diff} to reinforce foundations."
                )
            else:
                return (
                    curr_diff,
                    f"Reinforcing foundational practice at {curr_diff} with conceptual recommendations."
                )

        return curr_diff, f"Steady performance detected. Continuing practice at {curr_diff}."
