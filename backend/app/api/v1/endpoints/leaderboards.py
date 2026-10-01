"""Leaderboard Rankings API Endpoints."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_current_user_optional, get_db
from backend.app.models.user import User
from backend.app.services.gamification.leaderboard_service import (
    LeaderboardResponse,
    LeaderboardService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    category: str = Query(
        "weekly_xp",
        description="Leaderboard category: weekly_xp, monthly_xp, all_time_xp, streak",
    ),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Returns paginated privacy-safe competitive leaderboard rankings with deterministic tie-breaking."""
    user_id = current_user.id if current_user else None
    return await LeaderboardService.get_leaderboard(
        db=db,
        category=category,
        limit=limit,
        offset=offset,
        current_user_id=user_id,
    )


@router.get("/me")
async def get_my_rankings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns current user's rank across weekly, all-time, and streak leaderboards."""
    weekly = await LeaderboardService.get_leaderboard(
        db=db, category="weekly_xp", limit=100, current_user_id=current_user.id
    )
    all_time = await LeaderboardService.get_leaderboard(
        db=db, category="all_time_xp", limit=100, current_user_id=current_user.id
    )
    streak = await LeaderboardService.get_leaderboard(
        db=db, category="streak", limit=100, current_user_id=current_user.id
    )

    return {
        "weekly_xp": weekly.user_rank,
        "all_time_xp": all_time.user_rank,
        "streak": streak.user_rank,
    }
