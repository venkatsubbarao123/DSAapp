"""Progress tracking API endpoints for lessons, problems, topics, and overview."""

from typing import Optional
from fastapi import APIRouter, Depends, Request, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_current_user,
    get_db,
    get_progress_service,
    require_premium,
)
from backend.app.models.content import ContentStatus, Topic
from backend.app.models.user import User
from backend.app.schemas.progress import (
    MasteryInsightsRead,
    ProgressOverviewRead,
    TopicProgressRead,
    UserLessonProgressRead,
    UserProblemProgressRead,
)
from backend.app.services.progress_service import ProgressService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()


@router.get("/overview", response_model=dict)
async def get_progress_overview(
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Calculates comprehensive learning progress across all published educational material."""
    overview = await service.get_overview(current_user.id)
    return {"success": True, "data": overview.model_dump()}


@router.get("/topics", response_model=dict)
async def list_topics_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: ProgressService = Depends(get_progress_service),
):
    """Returns aggregated topic progress for all published topics."""
    stmt = select(Topic).where(Topic.status == ContentStatus.PUBLISHED).order_by(Topic.display_order.asc())
    topics = (await db.execute(stmt)).scalars().all()
    results = []
    for t in topics:
        prog = await service.repo.get_topic_progress(current_user.id, t.id)
        if prog:
            results.append(prog)
    return {"success": True, "data": results}


@router.get("/topics/{topic_id}", response_model=dict)
async def get_topic_progress(
    topic_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Returns aggregated topic progress derived directly from child lessons and problems."""
    topic_prog = await service.get_topic_progress(current_user.id, topic_id)
    return {"success": True, "data": topic_prog.model_dump()}


@router.get("/problems/{problem_id}", response_model=dict)
async def get_problem_progress(
    problem_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Returns current user's progress record for an individual problem."""
    prog = await service.get_problem_progress(current_user.id, problem_id)
    return {"success": True, "data": prog.model_dump()}


@router.get("/mastery", response_model=dict)
@router.get("/insights/mastery", response_model=dict)
async def get_mastery_insights(
    current_user: User = Depends(require_premium),
    service: ProgressService = Depends(get_progress_service),
):
    """Returns advanced learning mastery analytics and retention forecasting.
    
    CRITICAL ACCESS CONTROL:
    Server-authoritatively gated by require_premium.
    """
    insights = await service.get_mastery_insights(current_user.id)
    return {"success": True, "data": insights.model_dump()}


@router.post("/lessons/{lesson_id}/start", response_model=dict)
async def start_lesson(
    lesson_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Records that a user has begun reading a lesson."""
    await rate_limiter.check_rate_limit(f"prog:{current_user.id}", max_requests=120, window_seconds=60)
    prog = await service.start_lesson(current_user.id, lesson_id)
    return {"success": True, "data": prog.model_dump()}


@router.post("/lessons/{lesson_id}/complete", response_model=dict)
async def complete_lesson(
    lesson_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Marks a lesson completed."""
    await rate_limiter.check_rate_limit(f"prog:{current_user.id}", max_requests=120, window_seconds=60)
    prog = await service.complete_lesson(current_user.id, lesson_id)
    return {"success": True, "data": prog.model_dump()}


@router.post("/problems/{problem_id}/attempt", response_model=dict)
async def attempt_problem(
    problem_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Records problem attempt."""
    await rate_limiter.check_rate_limit(f"prog:{current_user.id}", max_requests=120, window_seconds=60)
    prog = await service.attempt_problem(current_user.id, problem_id)
    return {"success": True, "data": prog.model_dump()}


@router.post("/problems/{problem_id}/solve", response_model=dict)
async def solve_problem(
    problem_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Marks a problem solved."""
    await rate_limiter.check_rate_limit(f"prog:{current_user.id}", max_requests=120, window_seconds=60)
    prog = await service.solve_problem(current_user.id, problem_id)
    return {"success": True, "data": prog.model_dump()}
