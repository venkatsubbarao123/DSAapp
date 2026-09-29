"""Submission API endpoints for recording student code and viewing history."""

from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request, status

from backend.app.api.deps import (
    get_current_user,
    get_progress_service,
)
from backend.app.models.progress import SubmissionStatus
from backend.app.models.user import User
from backend.app.schemas.content import PaginatedData
from backend.app.schemas.progress import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionSummary,
)
from backend.app.services.progress_service import ProgressService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def submit_code(
    payload: SubmissionCreate,
    request: Request,
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Submits student source code for a problem.
    
    CRITICAL NON-GOAL & SECURITY INVARIANT:
    Phase 4 does NOT execute student code in-process or out-of-process.
    This endpoint verifies problem validity, enforces source code length caps (64KB),
    validates language allowlists, advances problem status to ATTEMPTED, and stores
    the submission for Phase 7 isolated containerized judge execution.
    """
    await rate_limiter.check_rate_limit(f"sub:{current_user.id}", max_requests=30, window_seconds=60)

    # Use header or body idempotency key
    effective_idempotency_key = idempotency_key_header or payload.idempotency_key
    payload.idempotency_key = effective_idempotency_key

    submission = await service.create_submission(current_user.id, payload)
    return {"success": True, "data": submission.model_dump()}


@router.get("", response_model=dict)
async def list_submissions(
    problem_id: Optional[str] = Query(None, description="Filter by problem slug or ID"),
    language: Optional[str] = Query(None, description="Filter by programming language"),
    status_filter: Optional[SubmissionStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Returns paginated list of current authenticated user's submissions.
    
    Source code is excluded from summary payloads for performance and privacy.
    """
    items, total = await service.list_submissions(
        user_id=current_user.id,
        problem_id=problem_id,
        language=language,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    paginated = PaginatedData[SubmissionSummary](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )
    return {"success": True, "data": paginated.model_dump()}


@router.get("/{submission_id}", response_model=dict)
async def get_submission_detail(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Retrieves full submission record including source code.
    
    STRICT IDOR DEFENSE: Strictly owner-only.
    """
    submission = await service.get_submission_detail(submission_id, current_user.id)
    return {"success": True, "data": submission.model_dump()}
