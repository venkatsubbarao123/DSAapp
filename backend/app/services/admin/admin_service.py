"""Admin service managing users, content test cases, system health diagnostics, and audit logs."""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.core.config import settings
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox import get_sandbox_diagnostics
from backend.app.models.audit import AuditLog
from backend.app.models.content import (
    Problem,
    ProblemDifficulty,
    ContentAccessLevel,
    ContentStatus,
    TestCase,
)
from backend.app.models.gamification import UserGamificationProfile
from backend.app.models.payment import PremiumEntitlement
from backend.app.models.progress import UserProblemProgress, ProblemProgressStatus, Submission
from backend.app.models.user import User, UserProfile, UserRole
from backend.app.schemas.admin import (
    AdminCreateTestCaseRequest,
    AdminProblemListItem,
    AdminProblemListResponse,
    AdminTestCaseItem,
    AdminUpdateTestCaseRequest,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    AuditLogItem,
    AuditLogListResponse,
    ServiceHealthStatus,
    SystemDiagnosticsResponse,
)
from backend.app.services.redis import redis_service

logger = logging.getLogger(__name__)

# Track process start time for uptime calculation
_PROCESS_START_TIME = time.time()


class AdminService:
    """Encapsulates administrative mutations and diagnostic queries with strict RBAC enforcement."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        plan: Optional[str] = None,
    ) -> AdminUserListResponse:
        """Paginated user listing with search, filtering, and subscription enrichment."""
        base_query = select(User).outerjoin(UserProfile, User.id == UserProfile.user_id)

        # Filters
        if search:
            search_term = f"%{search.strip().lower()}%"
            base_query = base_query.where(
                or_(
                    func.lower(User.email).like(search_term),
                    func.lower(UserProfile.display_name).like(search_term),
                )
            )
        if role:
            base_query = base_query.where(User.role == role)
        if is_active is not None:
            base_query = base_query.where(User.is_active == is_active)

        # Count total matching
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        # Pagination & sorting
        offset = (page - 1) * page_size
        items_stmt = (
            base_query.options(selectinload(User.profile))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(items_stmt)
        users = result.scalars().all()

        # Check premium entitlements in batch for current page
        user_ids = [u.id for u in users]
        now = datetime.now(timezone.utc)
        premium_user_ids = set()
        if user_ids:
            ent_stmt = select(PremiumEntitlement.user_id).where(
                PremiumEntitlement.user_id.in_(user_ids),
                PremiumEntitlement.is_active == True,
                PremiumEntitlement.expires_at > now,
            )
            ent_res = await self.db.execute(ent_stmt)
            premium_user_ids = {row[0] for row in ent_res.all()}

        items: List[AdminUserListItem] = []
        for u in users:
            is_prem = u.id in premium_user_ids
            # Filter by plan if requested
            user_plan = "PREMIUM" if is_prem else "FREE"
            if plan and user_plan != plan.upper():
                continue

            display_name = u.profile.display_name if u.profile and u.profile.display_name else u.email.split("@")[0]
            items.append(
                AdminUserListItem(
                    id=u.id,
                    email=u.email,
                    display_name=display_name,
                    role=u.role,
                    is_active=u.is_active,
                    is_verified=u.is_verified,
                    plan=user_plan,
                    premium_active=is_prem,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
            )

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return AdminUserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user_detail(self, user_id: str) -> AdminUserDetail:
        """Retrieves comprehensive user profile and cross-domain activity metrics."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.profile))
        )
        res = await self.db.execute(stmt)
        user = res.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Premium entitlement check
        now = datetime.now(timezone.utc)
        ent_stmt = (
            select(PremiumEntitlement)
            .where(
                PremiumEntitlement.user_id == user_id,
                PremiumEntitlement.is_active == True,
                PremiumEntitlement.expires_at > now,
            )
            .order_by(PremiumEntitlement.expires_at.desc())
        )
        ent_res = await self.db.execute(ent_stmt)
        ent = ent_res.scalars().first()
        is_premium = ent is not None
        plan = "PREMIUM" if is_premium else "FREE"
        expires_at = ent.expires_at if ent else None

        # Metrics: Submissions count
        sub_count_stmt = select(func.count(Submission.id)).where(Submission.user_id == user_id)
        sub_res = await self.db.execute(sub_count_stmt)
        submissions_count = sub_res.scalar() or 0

        # Metrics: Solved problems count
        solved_stmt = select(func.count(UserProblemProgress.id)).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.status == ProblemProgressStatus.SOLVED,
        )
        solved_res = await self.db.execute(solved_stmt)
        solved_count = solved_res.scalar() or 0

        # Metrics: Gamification stats
        gam_stmt = select(UserGamificationProfile).where(UserGamificationProfile.user_id == user_id)
        gam_res = await self.db.execute(gam_stmt)
        gam_profile = gam_res.scalars().first()
        current_streak = gam_profile.current_streak if gam_profile else 0
        total_xp = gam_profile.total_xp if gam_profile else 0

        display_name = user.profile.display_name if user.profile and user.profile.display_name else user.email.split("@")[0]
        bio = user.profile.bio if user.profile else None
        avatar_url = user.profile.avatar_url if user.profile else None

        return AdminUserDetail(
            id=user.id,
            email=user.email,
            display_name=display_name,
            bio=bio,
            avatar_url=avatar_url,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            plan=plan,
            premium_active=is_premium,
            premium_expires_at=expires_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            submissions_count=submissions_count,
            solved_problems_count=solved_count,
            current_streak=current_streak,
            total_xp=total_xp,
        )

    async def update_user_role(
        self,
        admin_user: User,
        target_user_id: str,
        new_role: UserRole,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AdminUserDetail:
        """Modifies a user's role with self-demotion protection and audit trail logging."""
        # Self-demotion guardrail
        if admin_user.id == target_user_id and new_role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot demote their own account role.",
            )

        stmt = select(User).where(User.id == target_user_id)
        res = await self.db.execute(stmt)
        target_user = res.scalars().first()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

        old_role = target_user.role
        target_user.role = new_role
        target_user.updated_at = datetime.now(timezone.utc)

        # Audit Log
        audit = AuditLog(
            actor_id=admin_user.id,
            action="admin.update_role",
            target_type="User",
            target_id=target_user_id,
            ip_address=ip_address,
            metadata_json=json.dumps({
                "old_role": old_role.value if hasattr(old_role, "value") else str(old_role),
                "new_role": new_role.value if hasattr(new_role, "value") else str(new_role),
                "reason": reason,
            }),
        )
        self.db.add(audit)
        await self.db.commit()

        logger.info(
            f"Admin {admin_user.id} updated user {target_user_id} role: {old_role} -> {new_role}"
        )
        return await self.get_user_detail(target_user_id)

    async def update_user_status(
        self,
        admin_user: User,
        target_user_id: str,
        is_active: bool,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AdminUserDetail:
        """Suspends or reactivates a user account with self-suspension guardrail."""
        # Self-suspension guardrail
        if admin_user.id == target_user_id and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot suspend their own account.",
            )

        stmt = select(User).where(User.id == target_user_id)
        res = await self.db.execute(stmt)
        target_user = res.scalars().first()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")

        old_status = target_user.is_active
        target_user.is_active = is_active
        target_user.updated_at = datetime.now(timezone.utc)

        action_name = "admin.reactivate_user" if is_active else "admin.suspend_user"
        audit = AuditLog(
            actor_id=admin_user.id,
            action=action_name,
            target_type="User",
            target_id=target_user_id,
            ip_address=ip_address,
            metadata_json=json.dumps({
                "old_active": old_status,
                "new_active": is_active,
                "reason": reason,
            }),
        )
        self.db.add(audit)
        await self.db.commit()

        logger.info(
            f"Admin {admin_user.id} updated user {target_user_id} active status: {old_status} -> {is_active}"
        )
        return await self.get_user_detail(target_user_id)

    # =========================================================================
    # PROBLEM & TEST CASE MANAGEMENT
    # =========================================================================

    async def list_problems(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        difficulty: Optional[ProblemDifficulty] = None,
        status_filter: Optional[ContentStatus] = None,
        access_level: Optional[ContentAccessLevel] = None,
    ) -> AdminProblemListResponse:
        """Administrative problem inventory listing with test case counts."""
        base_query = select(Problem)

        if search:
            search_term = f"%{search.strip().lower()}%"
            base_query = base_query.where(
                or_(
                    func.lower(Problem.title).like(search_term),
                    func.lower(Problem.slug).like(search_term),
                )
            )
        if difficulty:
            base_query = base_query.where(Problem.difficulty == difficulty)
        if status_filter:
            base_query = base_query.where(Problem.status == status_filter)
        if access_level:
            base_query = base_query.where(Problem.access_level == access_level)

        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        offset = (page - 1) * page_size
        items_stmt = (
            base_query.order_by(Problem.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        res = await self.db.execute(items_stmt)
        problems = res.scalars().all()

        # Count test cases for each problem
        prob_ids = [p.id for p in problems]
        tc_counts: Dict[str, int] = {}
        hidden_counts: Dict[str, int] = {}

        if prob_ids:
            tc_stmt = (
                select(TestCase.problem_id, func.count(TestCase.id))
                .where(TestCase.problem_id.in_(prob_ids))
                .group_by(TestCase.problem_id)
            )
            tc_res = await self.db.execute(tc_stmt)
            for pid, count in tc_res.all():
                tc_counts[pid] = count

            hidden_stmt = (
                select(TestCase.problem_id, func.count(TestCase.id))
                .where(TestCase.problem_id.in_(prob_ids), TestCase.is_hidden == True)
                .group_by(TestCase.problem_id)
            )
            hid_res = await self.db.execute(hidden_stmt)
            for pid, count in hid_res.all():
                hidden_counts[pid] = count

        items: List[AdminProblemListItem] = []
        for p in problems:
            items.append(
                AdminProblemListItem(
                    id=p.id,
                    public_id=p.public_id,
                    slug=p.slug,
                    title=p.title,
                    difficulty=p.difficulty,
                    access_level=p.access_level,
                    status=p.status,
                    time_limit_ms=p.time_limit_ms,
                    memory_limit_mb=p.memory_limit_mb,
                    test_cases_count=tc_counts.get(p.id, 0),
                    hidden_test_cases_count=hidden_counts.get(p.id, 0),
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return AdminProblemListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def list_test_cases(self, problem_id: str) -> List[AdminTestCaseItem]:
        """Lists ALL test cases for a problem (including hidden verification cases) for admin inspection."""
        prob_stmt = select(Problem).where(Problem.id == problem_id)
        prob_res = await self.db.execute(prob_stmt)
        if not prob_res.scalars().first():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        stmt = (
            select(TestCase)
            .where(TestCase.problem_id == problem_id)
            .order_by(TestCase.display_order.asc(), TestCase.created_at.asc())
        )
        res = await self.db.execute(stmt)
        test_cases = res.scalars().all()

        return [
            AdminTestCaseItem(
                id=tc.id,
                problem_id=tc.problem_id,
                input=tc.input,
                expected_output=tc.expected_output,
                is_sample=tc.is_sample,
                is_hidden=tc.is_hidden,
                display_order=tc.display_order,
                created_at=tc.created_at,
            )
            for tc in test_cases
        ]

    async def create_test_case(
        self,
        admin_user: User,
        problem_id: str,
        data: AdminCreateTestCaseRequest,
        ip_address: Optional[str] = None,
    ) -> AdminTestCaseItem:
        """Adds a new test case (public sample or hidden judge case) to a problem."""
        prob_stmt = select(Problem).where(Problem.id == problem_id)
        prob_res = await self.db.execute(prob_stmt)
        problem = prob_res.scalars().first()
        if not problem:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")

        tc = TestCase(
            problem_id=problem_id,
            input=data.input,
            expected_output=data.expected_output,
            is_sample=data.is_sample,
            is_hidden=data.is_hidden,
            display_order=data.display_order,
        )
        self.db.add(tc)

        audit = AuditLog(
            actor_id=admin_user.id,
            action="admin.create_test_case",
            target_type="TestCase",
            target_id=tc.id,
            ip_address=ip_address,
            metadata_json=json.dumps({
                "problem_id": problem_id,
                "is_sample": data.is_sample,
                "is_hidden": data.is_hidden,
                "display_order": data.display_order,
            }),
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(tc)

        logger.info(f"Admin {admin_user.id} created test case {tc.id} for problem {problem_id}")
        return AdminTestCaseItem(
            id=tc.id,
            problem_id=tc.problem_id,
            input=tc.input,
            expected_output=tc.expected_output,
            is_sample=tc.is_sample,
            is_hidden=tc.is_hidden,
            display_order=tc.display_order,
            created_at=tc.created_at,
        )

    async def update_test_case(
        self,
        admin_user: User,
        test_case_id: str,
        data: AdminUpdateTestCaseRequest,
        ip_address: Optional[str] = None,
    ) -> AdminTestCaseItem:
        """Updates parameters of an existing test case."""
        stmt = select(TestCase).where(TestCase.id == test_case_id)
        res = await self.db.execute(stmt)
        tc = res.scalars().first()
        if not tc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

        if data.input is not None:
            tc.input = data.input
        if data.expected_output is not None:
            tc.expected_output = data.expected_output
        if data.is_sample is not None:
            tc.is_sample = data.is_sample
        if data.is_hidden is not None:
            tc.is_hidden = data.is_hidden
        if data.display_order is not None:
            tc.display_order = data.display_order

        audit = AuditLog(
            actor_id=admin_user.id,
            action="admin.update_test_case",
            target_type="TestCase",
            target_id=tc.id,
            ip_address=ip_address,
            metadata_json=json.dumps({"updated_fields": [k for k, v in data.model_dump().items() if v is not None]}),
        )
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(tc)

        return AdminTestCaseItem(
            id=tc.id,
            problem_id=tc.problem_id,
            input=tc.input,
            expected_output=tc.expected_output,
            is_sample=tc.is_sample,
            is_hidden=tc.is_hidden,
            display_order=tc.display_order,
            created_at=tc.created_at,
        )

    async def delete_test_case(
        self,
        admin_user: User,
        test_case_id: str,
        ip_address: Optional[str] = None,
    ) -> bool:
        """Deletes a test case permanently."""
        stmt = select(TestCase).where(TestCase.id == test_case_id)
        res = await self.db.execute(stmt)
        tc = res.scalars().first()
        if not tc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found")

        problem_id = tc.problem_id
        await self.db.delete(tc)

        audit = AuditLog(
            actor_id=admin_user.id,
            action="admin.delete_test_case",
            target_type="TestCase",
            target_id=test_case_id,
            ip_address=ip_address,
            metadata_json=json.dumps({"problem_id": problem_id}),
        )
        self.db.add(audit)
        await self.db.commit()

        logger.info(f"Admin {admin_user.id} deleted test case {test_case_id} of problem {problem_id}")
        return True

    # =========================================================================
    # SYSTEM DIAGNOSTICS & AUDIT LOGS
    # =========================================================================

    async def get_system_diagnostics(self) -> SystemDiagnosticsResponse:
        """Runs health diagnostics across all core subsystems.

        CRITICAL SECURITY INVARIANT:
        Strictly zero sensitive configuration, secrets, DB passwords, or credentials exposed.
        """
        # 1. Database check
        t0 = time.time()
        db_healthy = False
        db_msg = None
        db_latency = 0.0
        try:
            res = await self.db.execute(select(1))
            val = res.scalar()
            db_healthy = (val == 1)
            db_latency = round((time.time() - t0) * 1000, 2)
            db_msg = "Connected and responding"
        except Exception as e:
            db_msg = f"Database query failed: {type(e).__name__}"

        db_status = ServiceHealthStatus(
            status="healthy" if db_healthy else "unhealthy",
            message=db_msg,
            latency_ms=db_latency,
        )

        # 2. Redis check
        t0 = time.time()
        redis_conn = bool(redis_service.is_connected)
        redis_latency = round((time.time() - t0) * 1000, 2)
        redis_status = ServiceHealthStatus(
            status="healthy" if redis_conn else "degraded",
            message="Redis cache online" if redis_conn else "Operating in memory-fallback mode",
            latency_ms=redis_latency,
        )

        # 3. Docker sandbox diagnostics
        sandbox_diag = get_sandbox_diagnostics()
        sandbox_available = sandbox_diag.get("available", False)
        sandbox_status = ServiceHealthStatus(
            status="healthy" if sandbox_available else "degraded",
            message=f"Sandbox mode: {sandbox_diag.get('mode', 'unknown')}",
            details={
                "driver": sandbox_diag.get("driver", "docker"),
                "status": sandbox_diag.get("status", "unknown"),
            },
        )

        # 4. Judge queue health
        queue_stats = await JudgeQueue.get_queue_stats(self.db)
        queue_status = ServiceHealthStatus(
            status="healthy",
            message="Queue processing operational",
            details=queue_stats,
        )

        # 5. AI provider check
        gemini_configured = bool(getattr(settings, "GEMINI_API_KEY", None))
        ai_status = ServiceHealthStatus(
            status="healthy",
            message="AI tutoring engine operational",
            details={
                "provider": "Gemini 2.5 Flash" if gemini_configured else "Mock AI Tutor",
                "mode": "production" if gemini_configured else "fallback",
            },
        )

        uptime = round(time.time() - _PROCESS_START_TIME, 1)

        return SystemDiagnosticsResponse(
            app_name=settings.PROJECT_NAME if hasattr(settings, "PROJECT_NAME") else "DSAapp",
            app_version="1.0.0-phase9",
            environment=getattr(settings, "ENVIRONMENT", "development"),
            server_time=datetime.now(timezone.utc),
            uptime_seconds=uptime,
            database=db_status,
            redis=redis_status,
            docker_sandbox=sandbox_status,
            judge_queue=queue_status,
            ai_provider=ai_status,
            current_migration_revision="7c139d4e5f6a",
        )

    async def list_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        action: Optional[str] = None,
        actor_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> AuditLogListResponse:
        """Filterable, paginated inspection of the immutable security audit trail."""
        base_query = select(AuditLog)

        if action:
            base_query = base_query.where(AuditLog.action.ilike(f"%{action}%"))
        if actor_id:
            base_query = base_query.where(AuditLog.actor_id == actor_id)
        if target_type:
            base_query = base_query.where(AuditLog.target_type == target_type)
        if target_id:
            base_query = base_query.where(AuditLog.target_id == target_id)

        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        offset = (page - 1) * page_size
        items_stmt = (
            base_query.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        res = await self.db.execute(items_stmt)
        logs = res.scalars().all()

        items = [
            AuditLogItem(
                id=log.id,
                actor_id=log.actor_id,
                action=log.action,
                target_type=log.target_type,
                target_id=log.target_id,
                ip_address=log.ip_address,
                request_id=log.request_id,
                metadata_json=log.metadata_json,
                created_at=log.created_at,
            )
            for log in logs
        ]

        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return AuditLogListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
