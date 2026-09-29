"""Pydantic schemas for Platform Analytics & Business Intelligence."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TimeSeriesPoint(BaseModel):
    """Generic timestamped numeric point for charting."""
    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    count: int = Field(..., description="Metric value")


class CategoryCount(BaseModel):
    """Categorical distribution pair."""
    category: str
    count: int
    percentage: Optional[float] = None


class PlatformOverviewMetrics(BaseModel):
    """High-level platform KPI summary."""
    total_users: int = 0
    active_users_dau: int = 0
    active_users_wau: int = 0
    active_users_mau: int = 0
    total_problems: int = 0
    total_submissions: int = 0
    total_accepted_submissions: int = 0
    platform_acceptance_rate: float = 0.0
    total_premium_subscribers: int = 0
    total_revenue_amount: float = 0.0
    currency: str = "INR"


class UserAnalyticsResponse(BaseModel):
    """User acquisition, activity, and retention analytics."""
    total_users: int
    active_users: int
    suspended_users: int
    verified_users: int
    role_distribution: List[CategoryCount]
    plan_distribution: List[CategoryCount]
    signups_last_30_days: List[TimeSeriesPoint]


class ProblemStatItem(BaseModel):
    """Problem-level performance statistics."""
    problem_id: str
    title: str
    difficulty: str
    total_attempts: int
    accepted_attempts: int
    pass_rate: float


class ContentAnalyticsResponse(BaseModel):
    """Content, curriculum, and problem-solving analytics."""
    total_problems: int
    problems_by_difficulty: List[CategoryCount]
    problems_by_access_level: List[CategoryCount]
    total_submissions: int
    verdict_distribution: List[CategoryCount]
    top_attempted_problems: List[ProblemStatItem]
    hardest_problems: List[ProblemStatItem]
    submissions_last_30_days: List[TimeSeriesPoint]


class GamificationAnalyticsResponse(BaseModel):
    """Practice, streak, and gamification analytics."""
    total_xp_distributed: int
    users_with_active_streaks: int
    longest_streak_record: int
    total_badges_unlocked: int
    streak_tier_distribution: List[CategoryCount]


class CompetitionAnalyticsResponse(BaseModel):
    """Contests, Interview simulation, and CP analytics."""
    total_contests: int
    total_contest_registrations: int
    total_contest_submissions: int
    total_mock_interviews: int
    average_interview_score: float
    total_sql_submissions: int


class JudgeAnalyticsResponse(BaseModel):
    """Online Judge runtime, throughput, and error metrics."""
    queue_depth: int
    running_jobs: int
    total_jobs_executed: int
    sandbox_status: str
    verdict_breakdown: List[CategoryCount]
    supported_languages: List[str]


class RevenueAnalyticsResponse(BaseModel):
    """Monetization and subscription metrics."""
    total_orders: int
    successful_orders: int
    failed_orders: int
    total_revenue: float
    currency: str
    active_subscriptions: int
    revenue_last_30_days: List[Dict[str, Any]]


class ComprehensiveAnalyticsResponse(BaseModel):
    """Aggregated dashboard payload for administrative analytics."""
    timestamp: datetime
    cached: bool = False
    overview: PlatformOverviewMetrics
    users: UserAnalyticsResponse
    content: ContentAnalyticsResponse
    gamification: GamificationAnalyticsResponse
    competition: CompetitionAnalyticsResponse
    judge: JudgeAnalyticsResponse
    revenue: RevenueAnalyticsResponse
