"""Analytics service aggregating platform metrics, content performance, judge operations, and revenue with Redis caching."""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox import get_sandbox_diagnostics
from backend.app.models.content import (
    Problem,
)
from backend.app.models.contest import Contest, ContestParticipant, ContestSubmission
from backend.app.models.gamification import (
    UserAchievement,
    UserGamificationProfile,
)
from backend.app.models.interview import InterviewSession, InterviewStatus
from backend.app.models.judge import JudgeJob
from backend.app.models.payment import OrderStatus, PaymentOrder, PremiumEntitlement
from backend.app.models.progress import Submission, SubmissionStatus
from backend.app.models.sql_learning import SQLSubmission
from backend.app.models.user import User
from backend.app.schemas.analytics import (
    CategoryCount,
    CompetitionAnalyticsResponse,
    ComprehensiveAnalyticsResponse,
    ContentAnalyticsResponse,
    GamificationAnalyticsResponse,
    JudgeAnalyticsResponse,
    PlatformOverviewMetrics,
    ProblemStatItem,
    RevenueAnalyticsResponse,
    TimeSeriesPoint,
    UserAnalyticsResponse,
)
from backend.app.services.redis import redis_service

logger = logging.getLogger(__name__)

REDIS_ANALYTICS_CACHE_KEY = "admin:analytics:comprehensive"
ANALYTICS_CACHE_TTL_SECONDS = 60


class AnalyticsService:
    """Computes authoritative real-world platform analytics across all subsystems."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_platform_overview(self) -> PlatformOverviewMetrics:
        """High-level platform KPI summary computed directly from DB."""
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(days=1)
        seven_days_ago = now - timedelta(days=7)
        thirty_days_ago = now - timedelta(days=30)

        # Total registered users
        u_res = await self.db.execute(select(func.count(User.id)))
        total_users = u_res.scalar() or 0

        # DAU: active in submissions or created in last 24h
        dau_stmt = select(func.count(func.distinct(Submission.user_id))).where(
            Submission.created_at >= one_day_ago
        )
        dau_res = await self.db.execute(dau_stmt)
        dau_submissions = dau_res.scalar() or 0
        new_users_dau = (
            await self.db.execute(
                select(func.count(User.id)).where(User.created_at >= one_day_ago)
            )
        ).scalar() or 0
        active_dau = max(dau_submissions, new_users_dau)

        # WAU
        wau_stmt = select(func.count(func.distinct(Submission.user_id))).where(
            Submission.created_at >= seven_days_ago
        )
        wau_submissions = (await self.db.execute(wau_stmt)).scalar() or 0
        new_users_wau = (
            await self.db.execute(
                select(func.count(User.id)).where(User.created_at >= seven_days_ago)
            )
        ).scalar() or 0
        active_wau = max(wau_submissions, new_users_wau)

        # MAU
        mau_stmt = select(func.count(func.distinct(Submission.user_id))).where(
            Submission.created_at >= thirty_days_ago
        )
        mau_submissions = (await self.db.execute(mau_stmt)).scalar() or 0
        new_users_mau = (
            await self.db.execute(
                select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
            )
        ).scalar() or 0
        active_mau = max(mau_submissions, new_users_mau)

        # Problems & Submissions
        prob_res = await self.db.execute(select(func.count(Problem.id)))
        total_problems = prob_res.scalar() or 0

        sub_res = await self.db.execute(select(func.count(Submission.id)))
        total_submissions = sub_res.scalar() or 0

        acc_res = await self.db.execute(
            select(func.count(Submission.id)).where(
                Submission.status == SubmissionStatus.ACCEPTED
            )
        )
        total_accepted = acc_res.scalar() or 0

        acceptance_rate = (
            round((total_accepted / total_submissions * 100), 1)
            if total_submissions > 0
            else 0.0
        )

        # Premium & Revenue
        prem_res = await self.db.execute(
            select(func.count(PremiumEntitlement.id)).where(
                PremiumEntitlement.is_active.is_(True),
                PremiumEntitlement.expires_at > now,
            )
        )
        total_premium = prem_res.scalar() or 0

        rev_res = await self.db.execute(
            select(func.sum(PaymentOrder.amount)).where(
                PaymentOrder.status == OrderStatus.SUCCESS
            )
        )
        cents_sum = rev_res.scalar() or 0
        total_rev = round(float(cents_sum) / 100.0, 2)

        return PlatformOverviewMetrics(
            total_users=total_users,
            active_users_dau=active_dau,
            active_users_wau=active_wau,
            active_users_mau=active_mau,
            total_problems=total_problems,
            total_submissions=total_submissions,
            total_accepted_submissions=total_accepted,
            platform_acceptance_rate=acceptance_rate,
            total_premium_subscribers=total_premium,
            total_revenue_amount=total_rev,
            currency="INR",
        )

    async def get_user_analytics(self) -> UserAnalyticsResponse:
        """User growth, verification, and role distributions."""
        u_res = await self.db.execute(select(func.count(User.id)))
        total_users = u_res.scalar() or 0

        active_res = await self.db.execute(
            select(func.count(User.id)).where(User.is_active.is_(True))
        )
        active_users = active_res.scalar() or 0

        susp_res = await self.db.execute(
            select(func.count(User.id)).where(User.is_active.is_(False))
        )
        suspended_users = susp_res.scalar() or 0

        ver_res = await self.db.execute(
            select(func.count(User.id)).where(User.is_verified.is_(True))
        )
        verified_users = ver_res.scalar() or 0

        # Roles
        role_stmt = select(User.role, func.count(User.id)).group_by(User.role)
        role_res = await self.db.execute(role_stmt)
        roles = [
            CategoryCount(
                category=r.value if hasattr(r, "value") else str(r),
                count=c,
                percentage=round((c / total_users * 100), 1)
                if total_users > 0
                else 0.0,
            )
            for r, c in role_res.all()
        ]

        # Plans
        now = datetime.now(timezone.utc)
        prem_res = await self.db.execute(
            select(func.count(func.distinct(PremiumEntitlement.user_id))).where(
                PremiumEntitlement.is_active.is_(True),
                PremiumEntitlement.expires_at > now,
            )
        )
        prem_count = prem_res.scalar() or 0
        free_count = max(0, total_users - prem_count)
        plans = [
            CategoryCount(
                category="FREE",
                count=free_count,
                percentage=round((free_count / total_users * 100), 1)
                if total_users > 0
                else 0.0,
            ),
            CategoryCount(
                category="PREMIUM",
                count=prem_count,
                percentage=round((prem_count / total_users * 100), 1)
                if total_users > 0
                else 0.0,
            ),
        ]

        # Signups last 30 days
        thirty_days_ago = now - timedelta(days=30)
        signups_stmt = (
            select(func.date(User.created_at), func.count(User.id))
            .where(User.created_at >= thirty_days_ago)
            .group_by(func.date(User.created_at))
            .order_by(func.date(User.created_at).asc())
        )
        signups_res = await self.db.execute(signups_stmt)
        signup_series = [
            TimeSeriesPoint(date=str(d), count=c) for d, c in signups_res.all()
        ]

        return UserAnalyticsResponse(
            total_users=total_users,
            active_users=active_users,
            suspended_users=suspended_users,
            verified_users=verified_users,
            role_distribution=roles,
            plan_distribution=plans,
            signups_last_30_days=signup_series,
        )

    async def get_content_analytics(self) -> ContentAnalyticsResponse:
        """Content difficulty distributions, submission verdicts, and hardest problems."""
        prob_res = await self.db.execute(select(func.count(Problem.id)))
        total_problems = prob_res.scalar() or 0

        # Difficulties
        diff_stmt = select(Problem.difficulty, func.count(Problem.id)).group_by(
            Problem.difficulty
        )
        diff_res = await self.db.execute(diff_stmt)
        diffs = [
            CategoryCount(
                category=d.value if hasattr(d, "value") else str(d),
                count=c,
                percentage=round((c / total_problems * 100), 1)
                if total_problems > 0
                else 0.0,
            )
            for d, c in diff_res.all()
        ]

        # Access levels
        acc_stmt = select(Problem.access_level, func.count(Problem.id)).group_by(
            Problem.access_level
        )
        acc_res = await self.db.execute(acc_stmt)
        accs = [
            CategoryCount(
                category=a.value if hasattr(a, "value") else str(a),
                count=c,
                percentage=round((c / total_problems * 100), 1)
                if total_problems > 0
                else 0.0,
            )
            for a, c in acc_res.all()
        ]

        # Submissions & Verdicts
        sub_res = await self.db.execute(select(func.count(Submission.id)))
        total_submissions = sub_res.scalar() or 0

        verd_stmt = select(Submission.status, func.count(Submission.id)).group_by(
            Submission.status
        )
        verd_res = await self.db.execute(verd_stmt)
        verdicts = [
            CategoryCount(
                category=v.value if hasattr(v, "value") else str(v),
                count=c,
                percentage=round((c / total_submissions * 100), 1)
                if total_submissions > 0
                else 0.0,
            )
            for v, c in verd_res.all()
        ]

        # Top attempted problems
        top_stmt = (
            select(
                Problem.id, Problem.title, Problem.difficulty, func.count(Submission.id)
            )
            .join(Submission, Problem.id == Submission.problem_id)
            .group_by(Problem.id, Problem.title, Problem.difficulty)
            .order_by(desc(func.count(Submission.id)))
            .limit(5)
        )
        top_res = await self.db.execute(top_stmt)
        top_problems: list[ProblemStatItem] = []
        for pid, title, diff, attempts in top_res.all():
            # Get accepted count
            acc_cnt_res = await self.db.execute(
                select(func.count(Submission.id)).where(
                    Submission.problem_id == pid,
                    Submission.status == SubmissionStatus.ACCEPTED,
                )
            )
            acc_cnt = acc_cnt_res.scalar() or 0
            pr = round((acc_cnt / attempts * 100), 1) if attempts > 0 else 0.0
            top_problems.append(
                ProblemStatItem(
                    problem_id=pid,
                    title=title,
                    difficulty=diff.value if hasattr(diff, "value") else str(diff),
                    total_attempts=attempts,
                    accepted_attempts=acc_cnt,
                    pass_rate=pr,
                )
            )

        # Hardest problems (at least 2 attempts)
        hard_stmt = (
            select(
                Problem.id, Problem.title, Problem.difficulty, func.count(Submission.id)
            )
            .join(Submission, Problem.id == Submission.problem_id)
            .group_by(Problem.id, Problem.title, Problem.difficulty)
            .having(func.count(Submission.id) >= 2)
            .limit(10)
        )
        hard_res = await self.db.execute(hard_stmt)
        hard_candidates: list[ProblemStatItem] = []
        for pid, title, diff, attempts in hard_res.all():
            acc_cnt_res = await self.db.execute(
                select(func.count(Submission.id)).where(
                    Submission.problem_id == pid,
                    Submission.status == SubmissionStatus.ACCEPTED,
                )
            )
            acc_cnt = acc_cnt_res.scalar() or 0
            pr = round((acc_cnt / attempts * 100), 1) if attempts > 0 else 0.0
            hard_candidates.append(
                ProblemStatItem(
                    problem_id=pid,
                    title=title,
                    difficulty=diff.value if hasattr(diff, "value") else str(diff),
                    total_attempts=attempts,
                    accepted_attempts=acc_cnt,
                    pass_rate=pr,
                )
            )
        hard_candidates.sort(key=lambda x: x.pass_rate)
        hardest_problems = hard_candidates[:5]

        # Submissions last 30 days
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        sub_series_stmt = (
            select(func.date(Submission.created_at), func.count(Submission.id))
            .where(Submission.created_at >= thirty_days_ago)
            .group_by(func.date(Submission.created_at))
            .order_by(func.date(Submission.created_at).asc())
        )
        sub_series_res = await self.db.execute(sub_series_stmt)
        submissions_series = [
            TimeSeriesPoint(date=str(d), count=c) for d, c in sub_series_res.all()
        ]

        return ContentAnalyticsResponse(
            total_problems=total_problems,
            problems_by_difficulty=diffs,
            problems_by_access_level=accs,
            total_submissions=total_submissions,
            verdict_distribution=verdicts,
            top_attempted_problems=top_problems,
            hardest_problems=hardest_problems,
            submissions_last_30_days=submissions_series,
        )

    async def get_gamification_analytics(self) -> GamificationAnalyticsResponse:
        """Aggregates XP issuance, streak health, and achievement milestones."""
        xp_res = await self.db.execute(
            select(func.sum(UserGamificationProfile.total_xp))
        )
        total_xp = xp_res.scalar() or 0

        streak_res = await self.db.execute(
            select(func.count(UserGamificationProfile.id)).where(
                UserGamificationProfile.current_streak > 0
            )
        )
        active_streaks = streak_res.scalar() or 0

        longest_res = await self.db.execute(
            select(func.max(UserGamificationProfile.longest_streak))
        )
        longest_record = longest_res.scalar() or 0

        badge_res = await self.db.execute(select(func.count(UserAchievement.id)))
        total_badges = badge_res.scalar() or 0

        # Streak tiers
        s1 = (
            await self.db.execute(
                select(func.count(UserGamificationProfile.id)).where(
                    UserGamificationProfile.current_streak.between(1, 7)
                )
            )
        ).scalar() or 0
        s2 = (
            await self.db.execute(
                select(func.count(UserGamificationProfile.id)).where(
                    UserGamificationProfile.current_streak.between(8, 30)
                )
            )
        ).scalar() or 0
        s3 = (
            await self.db.execute(
                select(func.count(UserGamificationProfile.id)).where(
                    UserGamificationProfile.current_streak > 30
                )
            )
        ).scalar() or 0

        streak_tiers = [
            CategoryCount(category="1–7 Days", count=s1),
            CategoryCount(category="8–30 Days", count=s2),
            CategoryCount(category="31+ Days", count=s3),
        ]

        return GamificationAnalyticsResponse(
            total_xp_distributed=total_xp,
            users_with_active_streaks=active_streaks,
            longest_streak_record=longest_record,
            total_badges_unlocked=total_badges,
            streak_tier_distribution=streak_tiers,
        )

    async def get_competition_analytics(self) -> CompetitionAnalyticsResponse:
        """Contests, Mock Interviews, and SQL practice metrics."""
        cnt_res = await self.db.execute(select(func.count(Contest.id)))
        total_contests = cnt_res.scalar() or 0

        part_res = await self.db.execute(select(func.count(ContestParticipant.id)))
        total_parts = part_res.scalar() or 0

        csub_res = await self.db.execute(select(func.count(ContestSubmission.id)))
        total_csubs = csub_res.scalar() or 0

        intv_res = await self.db.execute(select(func.count(InterviewSession.id)))
        total_intvs = intv_res.scalar() or 0

        avg_intv_res = await self.db.execute(
            select(func.avg(InterviewSession.score)).where(
                InterviewSession.status == InterviewStatus.COMPLETED
            )
        )
        avg_intv_score = round(avg_intv_res.scalar() or 0.0, 1)

        sql_res = await self.db.execute(select(func.count(SQLSubmission.id)))
        total_sql = sql_res.scalar() or 0

        return CompetitionAnalyticsResponse(
            total_contests=total_contests,
            total_contest_registrations=total_parts,
            total_contest_submissions=total_csubs,
            total_mock_interviews=total_intvs,
            average_interview_score=avg_intv_score,
            total_sql_submissions=total_sql,
        )

    async def get_judge_analytics(self) -> JudgeAnalyticsResponse:
        """Online Judge queue, execution counters, and sandbox health status."""
        queue_stats = await JudgeQueue.get_queue_stats(self.db)
        queue_depth = queue_stats.get("queue_depth", 0)
        running_jobs = queue_stats.get("running_count", 0)

        job_cnt_res = await self.db.execute(select(func.count(JudgeJob.id)))
        total_jobs = job_cnt_res.scalar() or 0

        sandbox_diag = get_sandbox_diagnostics()
        sandbox_status = (
            "healthy" if sandbox_diag.get("available", False) else "degraded"
        )

        verd_stmt = select(Submission.status, func.count(Submission.id)).group_by(
            Submission.status
        )
        verd_res = await self.db.execute(verd_stmt)
        verdicts = [
            CategoryCount(
                category=v.value if hasattr(v, "value") else str(v),
                count=c,
            )
            for v, c in verd_res.all()
        ]

        return JudgeAnalyticsResponse(
            queue_depth=queue_depth,
            running_jobs=running_jobs,
            total_jobs_executed=total_jobs,
            sandbox_status=sandbox_status,
            verdict_breakdown=verdicts,
            supported_languages=["python", "java", "cpp", "javascript"],
        )

    async def get_revenue_analytics(self) -> RevenueAnalyticsResponse:
        """Monetization, orders, and premium ARR/MRR metrics."""
        now = datetime.now(timezone.utc)
        ord_res = await self.db.execute(select(func.count(PaymentOrder.id)))
        total_orders = ord_res.scalar() or 0

        succ_res = await self.db.execute(
            select(func.count(PaymentOrder.id)).where(
                PaymentOrder.status == OrderStatus.SUCCESS
            )
        )
        successful_orders = succ_res.scalar() or 0

        fail_res = await self.db.execute(
            select(func.count(PaymentOrder.id)).where(
                PaymentOrder.status == OrderStatus.FAILED
            )
        )
        failed_orders = fail_res.scalar() or 0

        rev_res = await self.db.execute(
            select(func.sum(PaymentOrder.amount)).where(
                PaymentOrder.status == OrderStatus.SUCCESS
            )
        )
        amount_cents = rev_res.scalar() or 0
        total_revenue = round(float(amount_cents) / 100.0, 2)

        prem_res = await self.db.execute(
            select(func.count(PremiumEntitlement.id)).where(
                PremiumEntitlement.is_active.is_(True),
                PremiumEntitlement.expires_at > now,
            )
        )
        active_subs = prem_res.scalar() or 0

        return RevenueAnalyticsResponse(
            total_orders=total_orders,
            successful_orders=successful_orders,
            failed_orders=failed_orders,
            total_revenue=total_revenue,
            currency="INR",
            active_subscriptions=active_subs,
            revenue_last_30_days=[],
        )

    async def get_comprehensive_analytics(
        self, force_refresh: bool = False
    ) -> ComprehensiveAnalyticsResponse:
        """Unified dashboard aggregator with 60-second Redis caching."""
        if not force_refresh:
            cached_data = await redis_service.get(REDIS_ANALYTICS_CACHE_KEY)
            if cached_data:
                try:
                    parsed = json.loads(cached_data)
                    parsed["cached"] = True
                    return ComprehensiveAnalyticsResponse(**parsed)
                except Exception as e:
                    logger.warning(f"Failed to deserialize cached analytics: {e}")

        overview = await self.get_platform_overview()
        users = await self.get_user_analytics()
        content = await self.get_content_analytics()
        gamification = await self.get_gamification_analytics()
        competition = await self.get_competition_analytics()
        judge = await self.get_judge_analytics()
        revenue = await self.get_revenue_analytics()

        response = ComprehensiveAnalyticsResponse(
            timestamp=datetime.now(timezone.utc),
            cached=False,
            overview=overview,
            users=users,
            content=content,
            gamification=gamification,
            competition=competition,
            judge=judge,
            revenue=revenue,
        )

        try:
            payload = response.model_dump_json()
            await redis_service.set(
                REDIS_ANALYTICS_CACHE_KEY, payload, ex=ANALYTICS_CACHE_TTL_SECONDS
            )
        except Exception as e:
            logger.warning(f"Failed to cache analytics in Redis: {e}")

        return response
