"""Competitive Programming Arena API endpoints."""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
)
from backend.app.models.user import User
from backend.app.schemas.cp import (
    CPLeaderboardResponse,
    CPProblemDetail,
    CPProblemSummary,
    CPRatingProfile,
)
from backend.app.services.cp.cp_service import CPService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/bands")
async def get_rating_bands():
    """Returns the competitive programming rating bands."""
    return [
        {"name": "Div 3 (Novice)", "min_rating": 800, "max_rating": 1199, "color": "#3b82f6", "problem_count": 25},
        {"name": "Div 2 (Specialist)", "min_rating": 1200, "max_rating": 1599, "color": "#10b981", "problem_count": 40},
        {"name": "Div 1 (Expert)", "min_rating": 1600, "max_rating": 1999, "color": "#f59e0b", "problem_count": 35},
        {"name": "Grandmaster", "min_rating": 2000, "max_rating": 2600, "color": "#ef4444", "problem_count": 15},
    ]


@router.get("/problems", response_model=List[CPProblemSummary])
async def list_cp_problems(
    rating_band: Optional[int] = Query(None, description="Filter by rating band, e.g. 800, 1200, 1600, 2000"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: EASY, MEDIUM, HARD, EXPERT"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Lists competitive programming problems with rating bands and solved status."""
    user_id = current_user.id if current_user else None
    return await CPService.list_cp_problems(db, user_id, rating_band, difficulty)


@router.get("/problems/{slug}", response_model=CPProblemDetail)
async def get_cp_problem(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full CP problem statement with input/output format and constraints."""
    user_id = current_user.id if current_user else None
    problem = await CPService.get_cp_problem_detail(db, slug, user_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitive programming problem not found.",
        )
    return problem


@router.get("/profile", response_model=CPRatingProfile)
async def get_my_cp_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves competitive programming rating profile and title for current user."""
    return await CPService.get_user_profile(db, current_user.id)


@router.get("/leaderboard", response_model=CPLeaderboardResponse)
async def get_cp_leaderboard(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves competitive programming Elo rating leaderboard."""
    return await CPService.get_cp_leaderboard(db, limit)
