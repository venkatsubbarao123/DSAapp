"""Phase 9 Security, IDOR prevention, and RBAC defense-in-depth test suite."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_access_token
from backend.app.models.notification import Notification, NotificationType
from backend.app.models.user import User, UserRole


@pytest.fixture
async def sec_p9_users(db_session: AsyncSession):
    """Sets up two isolated students and an admin."""
    uid = uuid.uuid4().hex[:6]

    user_a = User(
        email=f"user_a_{uid}@example.com",
        hashed_password="hashed_pwd_a",
        role=UserRole.STUDENT,
        is_active=True,
    )
    user_b = User(
        email=f"user_b_{uid}@example.com",
        hashed_password="hashed_pwd_b",
        role=UserRole.STUDENT,
        is_active=True,
    )
    admin = User(
        email=f"admin_{uid}@dsaapp.internal",
        hashed_password="hashed_admin_pwd",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add_all([user_a, user_b, admin])
    await db_session.flush()

    # Create notification belonging exclusively to User A
    notif_a = Notification(
        user_id=user_a.id,
        type=NotificationType.SYSTEM_NOTICE,
        title="Secret Notice for User A",
        body="Private notification details.",
        is_read=False,
    )
    db_session.add(notif_a)
    await db_session.commit()

    token_a = create_access_token(user_a.id, user_a.role.value)
    token_b = create_access_token(user_b.id, user_b.role.value)
    token_admin = create_access_token(admin.id, admin.role.value)

    return {
        "user_a": user_a,
        "user_b": user_b,
        "admin": admin,
        "notif_a": notif_a,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


@pytest.mark.asyncio
async def test_notification_idor_cross_tenant_prevention(client: AsyncClient, sec_p9_users):
    """IDOR TEST: User B cannot mark User A's notification as read."""
    headers_b = {"Authorization": f"Bearer {sec_p9_users['token_b']}"}
    notif_a_id = sec_p9_users["notif_a"].id

    res = await client.patch(f"/api/v1/notifications/{notif_a_id}/read", headers=headers_b)
    # Must fail with 404 (Not Found in User B's scope), preventing enumeration
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_non_admin_cannot_broadcast_announcements(client: AsyncClient, sec_p9_users):
    """RBAC TEST: Regular student cannot invoke broadcast notification endpoint."""
    headers_student = {"Authorization": f"Bearer {sec_p9_users['token_b']}"}

    res = await client.post(
        "/api/v1/notifications/broadcast",
        headers=headers_student,
        json={
            "title": "Spam Announcement",
            "body": "Unauthorized message.",
            "channels": ["IN_APP"],
        },
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_access_diagnostics_or_audit(client: AsyncClient, sec_p9_users):
    """RBAC TEST: Regular student cannot inspect system diagnostics or security audit logs."""
    headers_student = {"Authorization": f"Bearer {sec_p9_users['token_a']}"}

    diag_res = await client.get("/api/v1/admin/system/diagnostics", headers=headers_student)
    assert diag_res.status_code == 403

    audit_res = await client.get("/api/v1/admin/system/audit", headers=headers_student)
    assert audit_res.status_code == 403


@pytest.mark.asyncio
async def test_non_admin_cannot_modify_user_roles_or_status(client: AsyncClient, sec_p9_users):
    """RBAC TEST: Regular student cannot escalate their own role or suspend other users."""
    headers_student = {"Authorization": f"Bearer {sec_p9_users['token_a']}"}
    user_a_id = sec_p9_users["user_a"].id
    user_b_id = sec_p9_users["user_b"].id

    role_res = await client.patch(
        f"/api/v1/admin/users/{user_a_id}/role",
        headers=headers_student,
        json={"role": "ADMIN"},
    )
    assert role_res.status_code == 403

    status_res = await client.patch(
        f"/api/v1/admin/users/{user_b_id}/status",
        headers=headers_student,
        json={"is_active": False},
    )
    assert status_res.status_code == 403
