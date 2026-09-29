"""Mistake notebook API endpoints for learner personal debugging and concept gap tracking."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status

from backend.app.api.deps import (
    get_current_user,
    get_progress_service,
)
from backend.app.models.progress import MistakeType
from backend.app.models.user import User
from backend.app.schemas.content import PaginatedData
from backend.app.schemas.progress import (
    MistakeCreate,
    MistakeRead,
    MistakeUpdate,
)
from backend.app.services.progress_service import ProgressService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_mistake(
    payload: MistakeCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Creates a new mistake entry in the learner's personal notebook."""
    await rate_limiter.check_rate_limit(f"mistake:{current_user.id}", max_requests=60, window_seconds=60)
    mistake = await service.create_mistake(current_user.id, payload)
    return {"success": True, "data": mistake.model_dump()}


@router.get("", response_model=dict)
async def list_mistakes(
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    mistake_type: Optional[MistakeType] = Query(None, description="Filter by pedagogical mistake type"),
    problem_id: Optional[str] = Query(None, description="Filter by problem slug or ID"),
    search: Optional[str] = Query(None, max_length=100, description="Search terms in title or description"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Returns paginated personal mistake notebook entries for the authenticated user."""
    items, total = await service.list_mistakes(
        user_id=current_user.id,
        is_resolved=is_resolved,
        mistake_type=mistake_type,
        problem_id=problem_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    paginated = PaginatedData[MistakeRead](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return {"success": True, "data": paginated.model_dump()}


@router.get("/{mistake_id}", response_model=dict)
async def get_mistake(
    mistake_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Retrieves a single mistake notebook record (Owner-only)."""
    mistake = await service.get_mistake(mistake_id, current_user.id)
    return {"success": True, "data": mistake.model_dump()}


@router.patch("/{mistake_id}", response_model=dict)
async def update_mistake(
    mistake_id: str,
    payload: MistakeUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Updates a mistake notebook record (title, description, correction, resolution status)."""
    await rate_limiter.check_rate_limit(f"mistake:{current_user.id}", max_requests=60, window_seconds=60)
    mistake = await service.update_mistake(mistake_id, current_user.id, payload)
    return {"success": True, "data": mistake.model_dump()}


@router.delete("/{mistake_id}", response_model=dict)
async def delete_mistake(
    mistake_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Deletes a mistake entry from the user's notebook."""
    await rate_limiter.check_rate_limit(f"mistake:{current_user.id}", max_requests=60, window_seconds=60)
    await service.delete_mistake(mistake_id, current_user.id)
    return {"success": True, "data": {"deleted": True}}
