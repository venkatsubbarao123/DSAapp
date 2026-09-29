"""Admin endpoints for monitoring and managing the online judge and sandbox."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db, require_admin
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.service import JudgeService
from backend.app.models.user import User

router = APIRouter()


@router.get("/health", response_model=dict)
async def get_judge_health(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: Retrieves judge worker queue metrics and sandbox runtime diagnostic info."""
    data = await JudgeService.get_admin_judge_health(db)
    return {"success": True, "data": data}


@router.get("/queue", response_model=dict)
async def get_judge_queue_status(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: Inspects judge queue depths and job statuses."""
    queue_stats = await JudgeQueue.get_queue_stats(db)
    return {"success": True, "data": queue_stats}


@router.post("/reclaim-stale", response_model=dict)
async def trigger_stale_job_reclamation(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: Manually triggers dead/stale job recovery."""
    reclaimed = await JudgeQueue.reclaim_stale_jobs(db, timeout_seconds=30)
    return {"success": True, "data": {"reclaimed_jobs": reclaimed}}
