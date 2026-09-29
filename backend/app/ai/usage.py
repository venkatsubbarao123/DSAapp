"""AI Usage Tracking and Quota Management.

Enforces server-side quota limits for Free vs. Premium tiers
and logs immutable audit telemetry for every AI interaction.
"""

from datetime import datetime, timedelta, timezone
import logging
from typing import Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models.ai import AIUsage

logger = logging.getLogger(__name__)


class AIUsageTracker:
    """Manages AI request limits, daily quota verification, and usage persistence."""

    @staticmethod
    async def check_quota(
        db: AsyncSession,
        user_id: str,
        is_premium: bool,
    ) -> Tuple[bool, int, int]:
        """Checks if learner has remaining daily AI quota.
        
        Returns:
            Tuple of (can_proceed, daily_used, daily_remaining)
        """
        now = datetime.now(timezone.utc)
        start_of_window = now - timedelta(hours=24)

        stmt = (
            select(func.count(AIUsage.id))
            .where(
                AIUsage.user_id == user_id,
                AIUsage.created_at >= start_of_window,
                AIUsage.success.is_(True),
            )
        )
        result = await db.execute(stmt)
        daily_used = result.scalar() or 0

        quota_limit = (
            settings.AI_PREMIUM_TIER_DAILY_LIMIT
            if is_premium
            else settings.AI_FREE_TIER_DAILY_LIMIT
        )

        remaining = max(0, quota_limit - daily_used)
        can_proceed = remaining > 0

        return can_proceed, daily_used, remaining

    @staticmethod
    async def record_usage(
        db: AsyncSession,
        user_id: str,
        request_type: str,
        provider: str,
        model: str,
        latency_ms: int,
        success: bool = True,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        error_message: Optional[str] = None,
    ) -> AIUsage:
        """Persists immutable usage record for audit and quota monitoring."""
        record = AIUsage(
            user_id=user_id,
            request_type=request_type,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message[:1000] if error_message else None,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record
