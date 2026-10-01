"""Gamification Profile, XP Ledger, Streak, and Achievement Endpoints."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.gamification import (
    Achievement,
    RatingHistory,
    UserAchievement,
    XPTransaction,
)
from backend.app.models.user import User
from backend.app.schemas.gamification import (
    AchievementItem,
    AchievementsResponse,
    GamificationProfileResponse,
    RatingHistoryItem,
    RatingResponse,
    StreakResponse,
    XPTransactionItem,
    XPTransactionsResponse,
)
from backend.app.services.gamification.achievement_service import AchievementService
from backend.app.services.gamification.level_service import LevelService
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=GamificationProfileResponse)
async def get_gamification_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns authoritative learner gamification profile including level, streak, and rating."""
    profile = await XPService.get_or_create_profile(db, current_user.id)
    prog = LevelService.calculate_progress(profile.total_xp)

    return GamificationProfileResponse(
        total_xp=profile.total_xp,
        current_level=prog.current_level,
        level_floor_xp=prog.level_floor_xp,
        level_ceiling_xp=prog.level_ceiling_xp,
        xp_in_level=prog.xp_in_current_level,
        xp_needed_for_next_level=prog.xp_needed_for_next_level,
        progress_percent=prog.progress_percent,
        current_streak=profile.current_streak,
        longest_streak=profile.longest_streak,
        current_rating=profile.current_rating,
        total_solves=profile.total_solves,
    )


@router.get("/xp", response_model=XPTransactionsResponse)
async def get_xp_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns paginated immutable XP ledger transactions for the learner."""
    count_stmt = select(func.count(XPTransaction.id)).where(
        XPTransaction.user_id == current_user.id
    )
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        select(XPTransaction)
        .where(XPTransaction.user_id == current_user.id)
        .order_by(desc(XPTransaction.created_at))
        .limit(limit)
        .offset(offset)
    )
    txs = (await db.execute(stmt)).scalars().all()

    items = [
        XPTransactionItem(
            id=t.id,
            event_type=t.event_type,
            source_id=t.source_id,
            amount=t.amount,
            created_at=t.created_at,
        )
        for t in txs
    ]
    return XPTransactionsResponse(total_count=total, transactions=items)


@router.get("/streak", response_model=StreakResponse)
async def get_streak_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns learner activity streak metrics and freeze counts."""
    profile = await XPService.get_or_create_profile(db, current_user.id)
    today_str = StreakService.get_today_str()
    active_today = profile.last_activity_date == today_str

    return StreakResponse(
        current_streak=profile.current_streak,
        longest_streak=profile.longest_streak,
        last_activity_date=profile.last_activity_date,
        streak_freeze_count=profile.streak_freeze_count,
        active_today=active_today,
    )


@router.get("/achievements", response_model=AchievementsResponse)
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns master achievement catalog with user unlock status and unlock dates."""
    await AchievementService.ensure_catalog_seeded(db)

    # 1. Fetch catalog
    catalog_stmt = select(Achievement).order_by(Achievement.tier, Achievement.xp_reward)
    achievements = (await db.execute(catalog_stmt)).scalars().all()

    # 2. Fetch user unlocks
    user_ach_stmt = select(UserAchievement).where(
        UserAchievement.user_id == current_user.id
    )
    user_achievements = (await db.execute(user_ach_stmt)).scalars().all()
    unlock_map = {ua.achievement_id: ua for ua in user_achievements}

    items = [
        AchievementItem(
            id=a.id,
            code=a.code,
            title=a.title,
            description=a.description,
            category=a.category,
            tier=a.tier,
            xp_reward=a.xp_reward,
            icon=a.icon,
            unlocked=a.id in unlock_map,
            unlocked_at=unlock_map[a.id].unlocked_at if a.id in unlock_map else None,
        )
        for a in achievements
    ]
    return AchievementsResponse(
        total_achievements=len(achievements),
        unlocked_count=len(user_achievements),
        achievements=items,
    )


@router.get("/rating", response_model=RatingResponse)
async def get_rating_overview(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns learner skill rating overview and chronological rating adjustments."""
    profile = await XPService.get_or_create_profile(db, current_user.id)

    stmt = (
        select(RatingHistory)
        .where(RatingHistory.user_id == current_user.id)
        .order_by(desc(RatingHistory.created_at))
        .limit(limit)
    )
    history = (await db.execute(stmt)).scalars().all()

    items = [
        RatingHistoryItem(
            id=h.id,
            previous_rating=h.previous_rating,
            new_rating=h.new_rating,
            change=h.change,
            reason=h.reason,
            created_at=h.created_at,
        )
        for h in history
    ]
    return RatingResponse(
        current_rating=profile.current_rating,
        history=items,
    )
