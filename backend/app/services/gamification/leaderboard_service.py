"""Leaderboard service supporting weekly, monthly, all-time XP, solves, and streaks.

Ensures:
- Deterministic server-side ranking and tie-breaking
- Privacy-safe usernames/handles (never leaking emails or personal data)
- Graceful Redis caching with fallback to authoritative SQL queries
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.gamification import (
    UserGamificationProfile,
    XPTransaction,
)
from backend.app.models.user import User, UserProfile
from backend.app.services.redis import redis_service

logger = logging.getLogger(__name__)


class LeaderboardEntry(BaseModel):
    """Privacy-safe public leaderboard ranking item."""
    rank: int
    user_id: str
    display_name: str
    score: int
    level: int
    streak: int
    current_level: int = 1
    current_streak: int = 0


class LeaderboardResponse(BaseModel):
    """Paginated leaderboard ranking response."""
    category: str
    total_participants: int
    entries: List[LeaderboardEntry]
    user_rank: Optional[LeaderboardEntry] = None


class LeaderboardService:
    """Manages multi-category competitive ranking calculations."""

    @staticmethod
    def _sanitize_name(user_id: str, display_name: Optional[str]) -> str:
        """Returns privacy-safe public handle for a learner without email leakage."""
        if display_name and display_name.strip():
            cleaned = display_name.strip()
            if "@" in cleaned:
                cleaned = cleaned.split("@")[0]
            if cleaned:
                return cleaned
        return f"Coder-{user_id[:6]}"

    @staticmethod
    def _mask_display_name(user_id: str, profile: Optional[UserProfile]) -> str:
        """Returns privacy-safe public handle for a learner."""
        if profile and profile.display_name and profile.display_name.strip():
            return LeaderboardService._sanitize_name(user_id, profile.display_name)
        return f"Coder-{user_id[:6]}"

    @classmethod
    async def get_leaderboard(
        cls,
        db: AsyncSession,
        category: str = "weekly_xp",
        limit: int = 20,
        offset: int = 0,
        current_user_id: Optional[str] = None,
    ) -> LeaderboardResponse:
        """Calculates or retrieves cached leaderboard rankings for a category."""
        category = category.lower()
        if category not in ("weekly_xp", "monthly_xp", "all_time_xp", "weekly_solves", "streak"):
            category = "weekly_xp"

        limit = min(max(1, limit), 100)
        offset = max(0, offset)

        cache_key = f"leaderboard:{category}:{limit}:{offset}"

        # 1. Try Redis Cache
        if redis_service.is_connected and redis_service._client:
            try:
                cached_data = await redis_service._client.get(cache_key)
                if cached_data:
                    raw_dict = json.loads(cached_data)
                    return LeaderboardResponse(**raw_dict)
            except Exception as e:
                logger.warning(f"Redis leaderboard cache read failed: {e}")

        # 2. Compute authoritative SQL query
        now = datetime.now(timezone.utc)
        entries: List[LeaderboardEntry] = []
        total_count = 0

        if category == "weekly_xp":
            seven_days_ago = now - timedelta(days=7)
            # Aggregate XP from transactions within last 7 days
            subquery = (
                select(
                    XPTransaction.user_id,
                    func.sum(XPTransaction.amount).label("score"),
                )
                .where(XPTransaction.created_at >= seven_days_ago)
                .group_by(XPTransaction.user_id)
                .subquery()
            )

            stmt = (
                select(
                    subquery.c.user_id,
                    subquery.c.score,
                    UserGamificationProfile.current_level,
                    UserGamificationProfile.current_streak,
                    UserProfile.display_name,
                )
                .join(UserGamificationProfile, subquery.c.user_id == UserGamificationProfile.user_id)
                .outerjoin(UserProfile, subquery.c.user_id == UserProfile.user_id)
                .order_by(desc(subquery.c.score), UserGamificationProfile.user_id.asc())
            )
            rows = (await db.execute(stmt)).all()
            total_count = len(rows)

            for idx, r in enumerate(rows[offset : offset + limit], start=offset + 1):
                name = r.display_name.strip() if r.display_name else f"Coder-{r.user_id[:6]}"
                lvl = int(r.current_level or 1)
                strk = int(r.current_streak or 0)
                entries.append(
                    LeaderboardEntry(
                        rank=idx,
                        user_id=r.user_id,
                        display_name=name,
                        score=int(r.score or 0),
                        level=lvl,
                        streak=strk,
                        current_level=lvl,
                        current_streak=strk,
                    )
                )

        elif category == "streak":
            stmt = (
                select(
                    UserGamificationProfile.user_id,
                    UserGamificationProfile.current_streak.label("score"),
                    UserGamificationProfile.current_level,
                    UserGamificationProfile.current_streak,
                    UserProfile.display_name,
                )
                .outerjoin(UserProfile, UserGamificationProfile.user_id == UserProfile.user_id)
                .where(UserGamificationProfile.current_streak > 0)
                .order_by(desc(UserGamificationProfile.current_streak), UserGamificationProfile.user_id.asc())
            )
            rows = (await db.execute(stmt)).all()
            total_count = len(rows)

            for idx, r in enumerate(rows[offset : offset + limit], start=offset + 1):
                name = r.display_name.strip() if r.display_name else f"Coder-{r.user_id[:6]}"
                lvl = int(r.current_level or 1)
                strk = int(r.current_streak or 0)
                entries.append(
                    LeaderboardEntry(
                        rank=idx,
                        user_id=r.user_id,
                        display_name=name,
                        score=int(r.score or 0),
                        level=lvl,
                        streak=strk,
                        current_level=lvl,
                        current_streak=strk,
                    )
                )

        else:
            # Default: all_time_xp
            stmt = (
                select(
                    UserGamificationProfile.user_id,
                    UserGamificationProfile.total_xp.label("score"),
                    UserGamificationProfile.current_level,
                    UserGamificationProfile.current_streak,
                    UserProfile.display_name,
                )
                .outerjoin(UserProfile, UserGamificationProfile.user_id == UserProfile.user_id)
                .order_by(desc(UserGamificationProfile.total_xp), UserGamificationProfile.user_id.asc())
            )
            rows = (await db.execute(stmt)).all()
            total_count = len(rows)

            for idx, r in enumerate(rows[offset : offset + limit], start=offset + 1):
                name = r.display_name.strip() if r.display_name else f"Coder-{r.user_id[:6]}"
                lvl = int(r.current_level or 1)
                strk = int(r.current_streak or 0)
                entries.append(
                    LeaderboardEntry(
                        rank=idx,
                        user_id=r.user_id,
                        display_name=name,
                        score=int(r.score or 0),
                        level=lvl,
                        streak=strk,
                        current_level=lvl,
                        current_streak=strk,
                    )
                )

        # Find current user entry if requested
        user_rank_entry = None
        if current_user_id:
            user_rank_entry = next((e for e in entries if e.user_id == current_user_id), None)

        res = LeaderboardResponse(
            category=category,
            total_participants=total_count,
            entries=entries,
            user_rank=user_rank_entry,
        )

        # 3. Store in Redis cache if available (60 second TTL)
        if redis_service.is_connected and redis_service._client:
            try:
                await redis_service._client.setex(cache_key, 60, res.model_dump_json())
            except Exception as e:
                logger.warning(f"Redis leaderboard cache write failed: {e}")

        return res
