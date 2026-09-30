from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
    get_progress_service,
)
from backend.app.core.config import settings
from backend.app.judge.runner import execute_submission_now, run_sample_test_cases
from backend.app.judge.service import JudgeService
from backend.app.models.progress import SubmissionStatus
from backend.app.models.user import User
from backend.app.schemas.content import PaginatedData
from backend.app.schemas.judge import RunCodeRequest, SubmissionResultRead
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
    background_tasks: BackgroundTasks,
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Submits student source code for a problem.
    
    CRITICAL NON-GOAL & SECURITY INVARIANT:
    Phase 4 does NOT execute student code synchronously in-process.
    This endpoint verifies problem validity, enforces source code length caps (64KB),
    validates language allowlists, advances problem status to ATTEMPTED, and stores
    the submission for isolated containerized judge execution.
    """
    await rate_limiter.check_rate_limit(f"sub:{current_user.id}", max_requests=30, window_seconds=60)

    # Use header or body idempotency key
    effective_idempotency_key = idempotency_key_header or payload.idempotency_key
    payload.idempotency_key = effective_idempotency_key

    submission = await service.create_submission(current_user.id, payload)

    # In non-test environments, trigger immediate judge processing via background task
    if settings.ENVIRONMENT != "test":
        background_tasks.add_task(execute_submission_now, submission.id)

    return {"success": True, "data": submission.model_dump()}


@router.post("/run", response_model=dict)
async def run_code(
    payload: RunCodeRequest,
    problem_id: str = Query(..., description="Problem UUID or slug"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Direct sample case RUN endpoint without mutating user progress or submissions."""
    rate_key = f"run:{current_user.id}" if current_user else "run:guest"
    await rate_limiter.check_rate_limit(rate_key, max_requests=60, window_seconds=60)
    result = await run_sample_test_cases(
        db=db,
        problem_id_or_slug=problem_id,
        language=payload.language,
        source_code=payload.source_code,
        custom_input=payload.custom_input,
    )
    return {"success": True, "data": result.model_dump()}



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


@router.get("/{submission_id}/result", response_model=dict)
async def get_submission_result(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves online judge execution result for a submission.
    
    STRICT IDOR DEFENSE: Strictly owner-only or staff.
    """
    result = await JudgeService.get_submission_result_safe(db, submission_id, current_user)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission result not found or judging pending.",
        )
    read_data = SubmissionResultRead.model_validate(result)
    return {"success": True, "data": read_data.model_dump()}


@router.post("/{submission_id}/cancel", response_model=dict)
async def cancel_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancels a queued submission before execution begins."""
    cancelled = await JudgeService.cancel_user_submission(db, submission_id, current_user)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Submission cannot be cancelled (already running or completed).",
        )
    return {"success": True, "message": "Submission cancelled successfully."}


@router.post("/{submission_id}/evaluate", response_model=dict)
async def evaluate_submission(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    service: ProgressService = Depends(get_progress_service),
):
    """Triggers immediate evaluation of a queued submission and returns updated details."""
    # Verify ownership
    await service.get_submission_detail(submission_id, current_user.id)
    await execute_submission_now(submission_id)
    updated = await service.get_submission_detail(submission_id, current_user.id)
    return {"success": True, "data": updated.model_dump()}

