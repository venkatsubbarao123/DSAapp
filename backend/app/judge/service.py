"""High-level Judge Service interface for submissions and results."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox.manager import get_sandbox_diagnostics
from backend.app.models.judge import SubmissionResult
from backend.app.models.progress import Submission
from backend.app.models.user import User


class JudgeService:
    """Orchestrates submission queueing, result retrieval, and access verification."""

    @staticmethod
    async def get_submission_result_safe(
        db: AsyncSession,
        submission_id: str,
        current_user: User,
    ) -> SubmissionResult | None:
        """Retrieves submission result ensuring ownership or staff privileges.

        Strict IDOR protection: Users can only view results of their own submissions.
        """
        stmt = select(Submission).where(Submission.id == submission_id)
        result = await db.execute(stmt)
        submission = result.scalars().first()

        if not submission:
            return None

        # IDOR check: only submission owner or admin can view results
        is_admin = (
            getattr(current_user, "is_admin", False)
            or getattr(current_user, "role", "") == "ADMIN"
        )
        if submission.user_id != current_user.id and not is_admin:
            return None

        stmt_res = select(SubmissionResult).where(
            SubmissionResult.submission_id == submission_id
        )
        res = await db.execute(stmt_res)
        return res.scalars().first()

    @staticmethod
    async def cancel_user_submission(
        db: AsyncSession,
        submission_id: str,
        current_user: User,
    ) -> bool:
        """Cancels a submission if it belongs to current_user and is in QUEUED state."""
        stmt = select(Submission).where(Submission.id == submission_id)
        result = await db.execute(stmt)
        submission = result.scalars().first()

        if not submission:
            return False

        is_admin = (
            getattr(current_user, "is_admin", False)
            or getattr(current_user, "role", "") == "ADMIN"
        )
        if submission.user_id != current_user.id and not is_admin:
            return False

        return await JudgeQueue.cancel(db, submission_id)

    @staticmethod
    async def get_admin_judge_health(db: AsyncSession) -> dict[str, Any]:
        """Returns judge queue metrics and sandbox runtime diagnostics."""
        queue_stats = await JudgeQueue.get_queue_stats(db)
        sandbox_diag = get_sandbox_diagnostics()

        return {
            "queue": queue_stats,
            "sandbox": sandbox_diag,
        }
