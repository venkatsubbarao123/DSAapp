"""Spaced revision queue API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status

from backend.app.api.deps import (
    get_current_user,
    get_progress_service,
)
from backend.app.models.user import User
from backend.app.schemas.content import PaginatedData
from backend.app.schemas.progress import (
    ReviewActionRequest,
    RevisionItemCreate,
    RevisionItemRead,
)
from backend.app.services.progress_service import ProgressService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()


@router.get("", response_model=dict)
async def list_due_revisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Retrieves due and upcoming spaced revision items for the authenticated user."""
    items, total = await service.list_due_revisions(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    paginated = PaginatedData[RevisionItemRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return {"success": True, "data": paginated.model_dump()}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_revision_item(
    payload: RevisionItemCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Adds a lesson, problem, or mistake to the user's spaced revision queue."""
    await rate_limiter.check_rate_limit(f"rev:{current_user.id}", max_requests=60, window_seconds=60)
    item = await service.create_revision_item(current_user.id, payload)
    return {"success": True, "data": item.model_dump()}


@router.post("/{revision_item_id}/review", response_model=dict)
async def review_revision_item(
    revision_item_id: str,
    payload: ReviewActionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Records learner self-assessment feedback and calculates the next due date.
    
    Allowed outcomes: AGAIN, HARD, GOOD, EASY.
    """
    await rate_limiter.check_rate_limit(f"rev:{current_user.id}", max_requests=120, window_seconds=60)
    reviewed_item = await service.review_revision_item(
        revision_item_id, current_user.id, payload
    )
    return {"success": True, "data": reviewed_item.model_dump()}
