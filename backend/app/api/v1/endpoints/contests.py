"""Contest API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
    get_progress_service,
)
from backend.app.models.user import User
from backend.app.schemas.contest import (
    ContestDetailResponse,
    ContestLeaderboardResponse,
    ContestSubmitRequest,
    ContestSubmitResponse,
    ContestSummaryResponse,
    UserContestHistoryEntry,
)
from backend.app.services.contest.contest_service import ContestService
from backend.app.services.progress_service import ProgressService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[ContestSummaryResponse])
async def list_contests(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    """Lists contests with server-authoritative status (UPCOMING, LIVE, ENDED)."""
    return await ContestService.list_contests(db, status_filter)


@router.get("/history", response_model=list[UserContestHistoryEntry])
async def get_my_contest_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves personal contest participation history for authenticated user."""
    return await ContestService.get_user_history(db, current_user.id)


@router.get("/{slug}", response_model=ContestDetailResponse)
async def get_contest(
    slug: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves detailed contest specification, problem catalog, and user registration state."""
    user_id = current_user.id if current_user else None
    contest = await ContestService.get_contest_detail(db, slug, user_id)
    if not contest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found.",
        )
    return contest


@router.post("/{slug}/join", response_model=dict)
async def join_contest(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Registers current user for a contest."""
    success, msg = await ContestService.join_contest(db, slug, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg,
        )
    return {"success": True, "message": msg}


@router.post(
    "/{slug}/submit",
    response_model=ContestSubmitResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_contest_solution(
    slug: str,
    payload: ContestSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    progress_service: ProgressService = Depends(get_progress_service),
):
    """Submits code for a contest problem; verified against server countdown and queued in Judge."""
    resp, err = await ContestService.submit_solution(
        db=db,
        slug_or_id=slug,
        user=current_user,
        payload=payload,
        progress_service=progress_service,
    )
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err,
        )
    return resp


@router.get("/{slug}/leaderboard", response_model=ContestLeaderboardResponse)
async def get_contest_leaderboard(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Returns real-time or final contest scoreboard with deterministic tie-breaking."""
    leaderboard = await ContestService.get_leaderboard(db, slug)
    if not leaderboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found.",
        )
    return leaderboard
