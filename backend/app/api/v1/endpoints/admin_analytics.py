"""Administrative endpoints for platform overview metrics and detailed subsystem analytics."""

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_analytics_service, require_admin
from backend.app.models.user import User
from backend.app.schemas.analytics import (
    ComprehensiveAnalyticsResponse,
    ContentAnalyticsResponse,
    JudgeAnalyticsResponse,
    PlatformOverviewMetrics,
    RevenueAnalyticsResponse,
    UserAnalyticsResponse,
)
from backend.app.services.admin.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/overview", response_model=PlatformOverviewMetrics)
async def get_platform_overview(
    current_user: User = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Admin-only: High-level KPI summary (DAU/WAU/MAU, problems, submissions, revenue)."""
    return await analytics_service.get_platform_overview()


@router.get("/comprehensive", response_model=ComprehensiveAnalyticsResponse)
async def get_comprehensive_analytics(
    force_refresh: bool = Query(default=False, description="Bypass Redis cache"),
    current_user: User = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Admin-only: Full cross-subsystem analytics aggregated with Redis caching."""
    return await analytics_service.get_comprehensive_analytics(force_refresh=force_refresh)


@router.get("/users", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    current_user: User = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Admin-only: User acquisition, role distribution, and verification rates."""
    return await analytics_service.get_user_analytics()


@router.get("/content", response_model=ContentAnalyticsResponse)
async def get_content_analytics(
    current_user: User = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Admin-only: Problem difficulty spread, verdict distributions, and hardest problems."""
    return await analytics_service.get_content_analytics()


@router.get("/judge", response_model=JudgeAnalyticsResponse)
async def get_judge_analytics(
    current_user: User = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Admin-only: Online Judge queue throughput, sandbox status, and execution metrics."""
    return await analytics_service.get_judge_analytics()


@router.get("/revenue", response_model=RevenueAnalyticsResponse)
async def get_revenue_analytics(
    current_user: User = Depends(require_admin),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """Admin-only: Completed payment orders, active premium subscribers, and gross revenue."""
    return await analytics_service.get_revenue_analytics()
