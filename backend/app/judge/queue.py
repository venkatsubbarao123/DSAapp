"""Durable queue management for online judge execution.

Supports SQL persistence with optional Redis acceleration.
Provides atomic job claims, heartbeats, and stale job reclamation.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.judge import JudgeJob, JudgeJobStatus
from backend.app.models.progress import Submission, SubmissionStatus
from backend.app.services.redis import redis_service

logger = logging.getLogger(__name__)

REDIS_JUDGE_QUEUE_KEY = "judge:queue"


class JudgeQueue:
    """Manages enqueueing, atomic claiming, and health monitoring of judge jobs."""

    @staticmethod
    async def enqueue(db: AsyncSession, submission_id: str) -> JudgeJob:
        """Enqueues a submission for asynchronous judge execution."""
        # Check if job already exists for this submission
        stmt = select(JudgeJob).where(JudgeJob.submission_id == submission_id)
        result = await db.execute(stmt)
        existing_job = result.scalars().first()

        now = datetime.now(timezone.utc)

        if existing_job:
            if existing_job.status in (JudgeJobStatus.QUEUED, JudgeJobStatus.RUNNING, JudgeJobStatus.CLAIMED):
                return existing_job
            # Reset existing job for re-execution
            existing_job.status = JudgeJobStatus.QUEUED
            existing_job.queued_at = now
            existing_job.started_at = None
            existing_job.completed_at = None
            existing_job.heartbeat_at = None
            existing_job.worker_id = None
            existing_job.failure_reason = None
            job = existing_job
        else:
            job = JudgeJob(
                submission_id=submission_id,
                status=JudgeJobStatus.QUEUED,
                queued_at=now,
            )
            db.add(job)

        # Update submission status to QUEUED_FOR_FUTURE_JUDGE
        sub_stmt = (
            update(Submission)
            .where(Submission.id == submission_id)
            .values(status=SubmissionStatus.QUEUED_FOR_FUTURE_JUDGE, updated_at=now)
        )
        await db.execute(sub_stmt)
        await db.commit()
        await db.refresh(job)

        # Notify Redis queue if connected
        if redis_service.is_connected and redis_service._client:
            try:
                client: Any = redis_service._client
                await client.lpush(REDIS_JUDGE_QUEUE_KEY, job.id)
            except Exception as e:
                logger.warning(f"Redis enqueue failed, relying on DB queue: {e}")

        return job

    @staticmethod
    async def claim_next_job(db: AsyncSession, worker_id: str) -> Optional[JudgeJob]:
        """Atomically claims the oldest queued job for execution by worker_id."""
        now = datetime.now(timezone.utc)

        # Select oldest QUEUED or RETRY_PENDING job
        # For Postgres, with_for_update(skip_locked=True) is used; for SQLite, standard select.
        stmt = (
            select(JudgeJob)
            .where(JudgeJob.status.in_([JudgeJobStatus.QUEUED, JudgeJobStatus.RETRY_PENDING]))
            .order_by(JudgeJob.queued_at.asc())
            .limit(1)
        )

        # SQLite does not support SKIP LOCKED; apply with_for_update only when supported
        bind = db.bind
        dialect_name = bind.dialect.name if bind else ""
        if dialect_name == "postgresql":
            stmt = stmt.with_for_update(skip_locked=True)

        result = await db.execute(stmt)
        job = result.scalars().first()

        if not job:
            return None

        # Atomically claim job
        job.status = JudgeJobStatus.RUNNING
        job.worker_id = worker_id
        job.started_at = now
        job.heartbeat_at = now
        job.attempt_count += 1

        # Update submission status to RUNNING
        sub_stmt = (
            update(Submission)
            .where(Submission.id == job.submission_id)
            .values(status=SubmissionStatus.RUNNING, updated_at=now)
        )
        await db.execute(sub_stmt)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def heartbeat(db: AsyncSession, job_id: str, worker_id: str) -> bool:
        """Updates worker heartbeat for a currently active job."""
        now = datetime.now(timezone.utc)
        stmt = (
            update(JudgeJob)
            .where(
                JudgeJob.id == job_id,
                JudgeJob.worker_id == worker_id,
                JudgeJob.status == JudgeJobStatus.RUNNING,
            )
            .values(heartbeat_at=now, updated_at=now)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @staticmethod
    async def reclaim_stale_jobs(db: AsyncSession, timeout_seconds: int = 30) -> int:
        """Recovers jobs whose workers crashed or failed to send a heartbeat."""
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(seconds=timeout_seconds)

        # Find timed out running jobs
        stmt = (
            select(JudgeJob)
            .where(
                JudgeJob.status == JudgeJobStatus.RUNNING,
                JudgeJob.heartbeat_at < threshold,
            )
        )
        result = await db.execute(stmt)
        stale_jobs = result.scalars().all()

        reclaimed = 0
        for job in stale_jobs:
            if job.attempt_count < job.max_attempts:
                job.status = JudgeJobStatus.RETRY_PENDING
                job.worker_id = None
                job.heartbeat_at = None
                logger.warning(
                    f"Requeued stale judge job {job.id} (attempt {job.attempt_count}/{job.max_attempts})"
                )
            else:
                job.status = JudgeJobStatus.FAILED
                job.completed_at = now
                job.failure_reason = "Job exceeded maximum execution attempts without worker heartbeat."
                # Mark submission as SYSTEM_ERROR
                sub_stmt = (
                    update(Submission)
                    .where(Submission.id == job.submission_id)
                    .values(status=SubmissionStatus.SYSTEM_ERROR, updated_at=now)
                )
                await db.execute(sub_stmt)
                logger.error(f"Marked judge job {job.id} as FAILED due to repeated worker timeouts.")
            reclaimed += 1

        if reclaimed > 0:
            await db.commit()

        return reclaimed

    @staticmethod
    async def cancel(db: AsyncSession, submission_id: str) -> bool:
        """Cancels a queued or retry-pending judge job."""
        now = datetime.now(timezone.utc)
        stmt = select(JudgeJob).where(JudgeJob.submission_id == submission_id)
        result = await db.execute(stmt)
        job = result.scalars().first()

        if not job or job.status in (JudgeJobStatus.COMPLETED, JudgeJobStatus.FAILED):
            return False

        # Can only cancel if not actively running or completed
        if job.status in (JudgeJobStatus.QUEUED, JudgeJobStatus.RETRY_PENDING):
            job.status = JudgeJobStatus.CANCELLED
            job.completed_at = now
            job.failure_reason = "Cancelled by user."

            sub_stmt = (
                update(Submission)
                .where(Submission.id == submission_id)
                .values(status=SubmissionStatus.CANCELLED, updated_at=now)
            )
            await db.execute(sub_stmt)
            await db.commit()
            return True

        return False

    @staticmethod
    async def get_queue_stats(db: AsyncSession) -> Dict[str, Any]:
        """Provides operational metrics on queue depth and processing status."""
        stmt = select(JudgeJob.status, func.count(JudgeJob.id)).group_by(JudgeJob.status)
        result = await db.execute(stmt)
        counts = {status.value if hasattr(status, "value") else str(status): count for status, count in result.all()}

        total_queued = counts.get(JudgeJobStatus.QUEUED.value, 0) + counts.get(JudgeJobStatus.RETRY_PENDING.value, 0)
        total_running = counts.get(JudgeJobStatus.RUNNING.value, 0)

        return {
            "queue_depth": total_queued,
            "running_count": total_running,
            "status_breakdown": counts,
        }
