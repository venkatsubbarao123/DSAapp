"""Admin Analytics, System Diagnostics, and Audit Log test suite for Phase 9."""

import json
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_access_token
from backend.app.models.audit import AuditLog
from backend.app.models.content import Problem, ProblemDifficulty, ContentAccessLevel, ContentStatus
from backend.app.models.payment import PaymentOrder, OrderStatus
from backend.app.models.progress import Submission, SubmissionStatus
from backend.app.models.user import User, UserRole


@pytest.fixture
async def analytics_setup(db_session: AsyncSession):
    """Sets up an admin, a regular user, some problems, submissions, payments, and audit logs."""
    uid = uuid.uuid4().hex[:6]

    admin = User(
        email=f"admin_stat_{uid}@dsaapp.internal",
        hashed_password="hashed_admin_pwd",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student = User(
        email=f"student_stat_{uid}@example.com",
        hashed_password="hashed_student_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([admin, student])
    await db_session.flush()

    prob = Problem(
        slug=f"analytics-prob-{uid}",
        title="Analytics Problem",
        statement="Problem statement for metrics verification.",
        difficulty=ProblemDifficulty.MEDIUM,
        access_level=ContentAccessLevel.FREE,
        status=ContentStatus.PUBLISHED,
    )
    db_session.add(prob)
    await db_session.flush()

    # Submissions: 1 Accepted, 1 Wrong Answer
    sub1 = Submission(
        user_id=student.id,
        problem_id=prob.id,
        source_code="print('ok')",
        language="python",
        status=SubmissionStatus.ACCEPTED,
    )
    sub2 = Submission(
        user_id=student.id,
        problem_id=prob.id,
        source_code="print('fail')",
        language="python",
        status=SubmissionStatus.WRONG_ANSWER,
    )
    db_session.add_all([sub1, sub2])

    # Payment order
    order = PaymentOrder(
        user_id=student.id,
        plan_id="plan_premium_monthly",
        amount=49900,  # 499.00 INR
        currency="INR",
        status=OrderStatus.SUCCESS,
        provider="razorpay",
    )
    db_session.add(order)

    # Audit log
    audit = AuditLog(
        actor_id=admin.id,
        action="admin.diagnostics_test",
        target_type="System",
        target_id="diag_1",
        metadata_json=json.dumps({"detail": "test execution"}),
    )
    db_session.add(audit)
    await db_session.commit()

    admin_token = create_access_token(admin.id, admin.role.value)
    student_token = create_access_token(student.id, student.role.value)

    return {
        "admin": admin,
        "student": student,
        "problem": prob,
        "admin_token": admin_token,
        "student_token": student_token,
    }


@pytest.mark.asyncio
async def test_admin_overview_metrics(client: AsyncClient, analytics_setup):
    """Verifies that platform overview returns accurate aggregated counts from real DB."""
    headers = {"Authorization": f"Bearer {analytics_setup['admin_token']}"}

    res = await client.get("/api/v1/admin/overview", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] >= 2
    assert data["total_problems"] >= 1
    assert data["total_submissions"] >= 2
    assert data["total_accepted_submissions"] >= 1
    assert data["total_revenue_amount"] >= 499.0


@pytest.mark.asyncio
async def test_admin_comprehensive_analytics(client: AsyncClient, analytics_setup):
    """Tests comprehensive analytics payload and Redis caching flag."""
    headers = {"Authorization": f"Bearer {analytics_setup['admin_token']}"}

    # Initial call
    res = await client.get("/api/v1/admin/comprehensive?force_refresh=true", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["cached"] is False
    assert "overview" in data
    assert "users" in data
    assert "content" in data
    assert "gamification" in data
    assert "competition" in data
    assert "judge" in data
    assert "revenue" in data


@pytest.mark.asyncio
async def test_system_diagnostics_and_zero_secret_leakage(client: AsyncClient, analytics_setup):
    """CRITICAL SECURITY TEST: Verifies system health endpoint has ZERO secret leakage."""
    headers = {"Authorization": f"Bearer {analytics_setup['admin_token']}"}

    res = await client.get("/api/v1/admin/system/diagnostics", headers=headers)
    assert res.status_code == 200
    diag = res.json()

    assert diag["database"]["status"] in ("healthy", "degraded")
    assert diag["redis"]["status"] in ("healthy", "degraded")
    assert diag["docker_sandbox"]["status"] in ("healthy", "degraded")
    assert diag["judge_queue"]["status"] in ("healthy", "degraded")
    assert diag["ai_provider"]["status"] in ("healthy", "degraded")
    assert "current_migration_revision" in diag

    # Strictly verify that no sensitive configuration values leak into the response JSON
    raw_text = res.text.lower()
    assert "secret_key" not in raw_text
    assert "password" not in raw_text
    assert "private_key" not in raw_text


@pytest.mark.asyncio
async def test_admin_audit_logs_query(client: AsyncClient, analytics_setup):
    """Tests querying and filtering security audit logs."""
    headers = {"Authorization": f"Bearer {analytics_setup['admin_token']}"}

    res = await client.get("/api/v1/admin/system/audit?action=diagnostics_test", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    items = data["items"]
    assert items[0]["action"] == "admin.diagnostics_test"
    assert items[0]["actor_id"] == analytics_setup["admin"].id
