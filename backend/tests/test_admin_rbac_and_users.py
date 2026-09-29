"""Admin RBAC, User Management, and Safety Guardrails test suite for Phase 9."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_access_token
from backend.app.models.audit import AuditLog
from backend.app.models.user import User, UserProfile, UserRole


@pytest.fixture
async def admin_and_users(db_session: AsyncSession):
    """Sets up an admin user, a content editor, and regular student users."""
    uid = uuid.uuid4().hex[:6]

    admin = User(
        email=f"admin_{uid}@dsaapp.internal",
        hashed_password="hashed_admin_pwd",
        role=UserRole.ADMIN,
        is_active=True,
    )
    editor = User(
        email=f"editor_{uid}@dsaapp.internal",
        hashed_password="hashed_editor_pwd",
        role=UserRole.CONTENT_EDITOR,
        is_active=True,
    )
    student1 = User(
        email=f"student1_{uid}@example.com",
        hashed_password="hashed_student1_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    student2 = User(
        email=f"student2_{uid}@example.com",
        hashed_password="hashed_student2_pwd",
        role=UserRole.STUDENT,
        is_active=False,
    )
    db_session.add_all([admin, editor, student1, student2])
    await db_session.flush()

    prof1 = UserProfile(user_id=student1.id, display_name="Alice Student", bio="Learning DSA")
    prof2 = UserProfile(user_id=student2.id, display_name="Bob Suspended", bio="Inactive user")
    prof_admin = UserProfile(user_id=admin.id, display_name="Admin Chief", bio="Platform Admin")
    db_session.add_all([prof1, prof2, prof_admin])
    await db_session.commit()

    admin_token = create_access_token(admin.id, admin.role.value)
    editor_token = create_access_token(editor.id, editor.role.value)
    student_token = create_access_token(student1.id, student1.role.value)

    return {
        "admin": admin,
        "editor": editor,
        "student1": student1,
        "student2": student2,
        "admin_token": admin_token,
        "editor_token": editor_token,
        "student_token": student_token,
    }


@pytest.mark.asyncio
async def test_admin_users_rbac_enforcement(client: AsyncClient, admin_and_users):
    """Verifies that non-admin accounts cannot access user administrative endpoints."""
    # Unauthenticated -> 401
    res = await client.get("/api/v1/admin/users")
    assert res.status_code == 401

    # Student -> 403 Forbidden
    res = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_and_users['student_token']}"},
    )
    assert res.status_code == 403

    # Editor -> 403 Forbidden
    res = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_and_users['editor_token']}"},
    )
    assert res.status_code == 403

    # Admin -> 200 OK
    res = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_and_users['admin_token']}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 4


@pytest.mark.asyncio
async def test_admin_list_users_filters_and_search(client: AsyncClient, admin_and_users):
    """Tests search and status filtering in admin user catalog."""
    headers = {"Authorization": f"Bearer {admin_and_users['admin_token']}"}

    # Filter by search string (student1's unique email)
    res = await client.get(f"/api/v1/admin/users?search={admin_and_users['student1'].email}", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["email"] == admin_and_users["student1"].email

    # Filter by is_active=false
    res_inactive = await client.get("/api/v1/admin/users?is_active=false", headers=headers)
    assert res_inactive.status_code == 200
    inactive_items = res_inactive.json()["items"]
    assert any(u["id"] == admin_and_users["student2"].id for u in inactive_items)


@pytest.mark.asyncio
async def test_admin_get_user_detail(client: AsyncClient, admin_and_users):
    """Tests retrieving full user profile and activity metrics."""
    headers = {"Authorization": f"Bearer {admin_and_users['admin_token']}"}
    target_id = admin_and_users["student1"].id

    res = await client.get(f"/api/v1/admin/users/{target_id}", headers=headers)
    assert res.status_code == 200
    detail = res.json()
    assert detail["id"] == target_id
    assert detail["email"] == admin_and_users["student1"].email
    assert detail["display_name"] == "Alice Student"
    assert "submissions_count" in detail
    assert "solved_problems_count" in detail


@pytest.mark.asyncio
async def test_admin_update_user_role_and_audit(client: AsyncClient, admin_and_users, db_session: AsyncSession):
    """Tests role mutation and verifies immutable audit log creation."""
    headers = {"Authorization": f"Bearer {admin_and_users['admin_token']}"}
    target_id = admin_and_users["student1"].id

    # Promote student1 to CONTENT_EDITOR
    res = await client.patch(
        f"/api/v1/admin/users/{target_id}/role",
        headers=headers,
        json={"role": "CONTENT_EDITOR", "reason": "Promoted to editorial board"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "CONTENT_EDITOR"

    # Verify audit log entry
    stmt = select(AuditLog).where(AuditLog.target_id == target_id, AuditLog.action == "admin.update_role")
    audit_res = await db_session.execute(stmt)
    log = audit_res.scalars().first()
    assert log is not None
    assert log.actor_id == admin_and_users["admin"].id
    assert "CONTENT_EDITOR" in log.metadata_json


@pytest.mark.asyncio
async def test_admin_self_demotion_guardrail(client: AsyncClient, admin_and_users):
    """Admin cannot demote their own account role."""
    headers = {"Authorization": f"Bearer {admin_and_users['admin_token']}"}
    admin_id = admin_and_users["admin"].id

    res = await client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        headers=headers,
        json={"role": "STUDENT", "reason": "Accidental self demotion"},
    )
    assert res.status_code == 400
    err_text = str(res.json().get("error", {}).get("message", res.json().get("detail", ""))).lower()
    assert "cannot demote their own account" in err_text


@pytest.mark.asyncio
async def test_admin_update_user_status_and_guardrail(client: AsyncClient, admin_and_users):
    """Tests suspending a user and verifies self-suspension guardrail."""
    headers = {"Authorization": f"Bearer {admin_and_users['admin_token']}"}
    student_id = admin_and_users["student1"].id
    admin_id = admin_and_users["admin"].id

    # Suspend student
    res = await client.patch(
        f"/api/v1/admin/users/{student_id}/status",
        headers=headers,
        json={"is_active": False, "reason": "Terms of service violation"},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Admin self-suspension guardrail
    res_self = await client.patch(
        f"/api/v1/admin/users/{admin_id}/status",
        headers=headers,
        json={"is_active": False, "reason": "Self suspension attempt"},
    )
    assert res_self.status_code == 400
    err_text_self = str(res_self.json().get("error", {}).get("message", res_self.json().get("detail", ""))).lower()
    assert "cannot suspend their own account" in err_text_self

