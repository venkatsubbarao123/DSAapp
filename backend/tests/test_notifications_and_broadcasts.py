"""Notification dispatch, channel preferences, deduplication, and admin broadcast test suite."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import create_access_token
from backend.app.models.audit import AuditLog
from backend.app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationType,
)
from backend.app.models.user import User, UserRole
from backend.app.services.notification.email_provider import MockEmailProvider, set_email_provider
from backend.app.services.notification.notification_service import NotificationService


@pytest.fixture
async def notif_setup(db_session: AsyncSession):
    """Sets up an admin and student user with fresh MockEmailProvider."""
    uid = uuid.uuid4().hex[:6]
    mock_email = MockEmailProvider()
    set_email_provider(mock_email)

    admin = User(
        email=f"admin_notif_{uid}@dsaapp.internal",
        hashed_password="hashed_admin_pwd",
        role=UserRole.ADMIN,
        is_active=True,
    )
    student = User(
        email=f"student_notif_{uid}@example.com",
        hashed_password="hashed_student_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add_all([admin, student])
    await db_session.flush()

    # Create initial notification for student
    svc = NotificationService(db_session)
    n1 = await svc.create_notification(
        user_id=student.id,
        notification_type=NotificationType.ACHIEVEMENT_UNLOCKED,
        title="Badge Unlocked!",
        body="You unlocked the First Solve badge.",
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    )

    admin_token = create_access_token(admin.id, admin.role.value)
    student_token = create_access_token(student.id, student.role.value)

    return {
        "admin": admin,
        "student": student,
        "initial_notif": n1,
        "mock_email": mock_email,
        "admin_token": admin_token,
        "student_token": student_token,
    }


@pytest.mark.asyncio
async def test_user_notification_list_and_unread_count(client: AsyncClient, notif_setup):
    """Verifies notification listing and topbar badge unread count."""
    headers = {"Authorization": f"Bearer {notif_setup['student_token']}"}

    # Unread count
    cnt_res = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res.status_code == 200
    assert cnt_res.json()["unread_count"] >= 1

    # List notifications
    list_res = await client.get("/api/v1/notifications", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert data["unread_count"] >= 1
    assert data["items"][0]["title"] == "Badge Unlocked!"


@pytest.mark.asyncio
async def test_mark_as_read_and_mark_all_read(client: AsyncClient, notif_setup):
    """Tests single notification read mutation and bulk read-all."""
    headers = {"Authorization": f"Bearer {notif_setup['student_token']}"}
    nid = notif_setup["initial_notif"].id

    # Mark single as read
    read_res = await client.patch(f"/api/v1/notifications/{nid}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] is True

    # Unread count should now be 0
    cnt_res = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert cnt_res.status_code == 200
    assert cnt_res.json()["unread_count"] == 0

    # Mark all read
    bulk_res = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert bulk_res.status_code == 200
    assert "marked_count" in bulk_res.json()


@pytest.mark.asyncio
async def test_notification_preferences_management(client: AsyncClient, notif_setup):
    """Tests fetching and updating user notification preference toggles."""
    headers = {"Authorization": f"Bearer {notif_setup['student_token']}"}

    # Fetch preferences
    pref_res = await client.get("/api/v1/notifications/preferences", headers=headers)
    assert pref_res.status_code == 200
    prefs = pref_res.json()["preferences"]
    assert len(prefs) > 0

    # Disable EMAIL for STREAK_REMINDER
    update_res = await client.put(
        "/api/v1/notifications/preferences",
        headers=headers,
        json={
            "preferences": [
                {
                    "channel": "EMAIL",
                    "notification_type": "STREAK_REMINDER",
                    "is_enabled": False,
                }
            ]
        },
    )
    assert update_res.status_code == 200
    updated_prefs = update_res.json()["preferences"]
    target = next(
        p for p in updated_prefs
        if p["channel"] == "EMAIL" and p["notification_type"] == "STREAK_REMINDER"
    )
    assert target["is_enabled"] is False


@pytest.mark.asyncio
async def test_deduplication_and_email_delivery(db_session: AsyncSession, notif_setup):
    """Verifies deduplication key suppresses duplicate notifications and email provider logs."""
    svc = NotificationService(db_session)
    student_id = notif_setup["student"].id
    dedup_key = f"streak_reminder:{student_id}:2026-09-30"

    # First dispatch -> created
    n1 = await svc.create_notification(
        user_id=student_id,
        notification_type=NotificationType.STREAK_REMINDER,
        title="Keep your streak alive!",
        body="Solve 1 problem today.",
        deduplication_key=dedup_key,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    )
    assert n1 is not None

    # Second dispatch with identical key -> deduplicated, returns same record without duplicate email
    initial_email_count = len(notif_setup["mock_email"].sent_messages)
    n2 = await svc.create_notification(
        user_id=student_id,
        notification_type=NotificationType.STREAK_REMINDER,
        title="Keep your streak alive!",
        body="Solve 1 problem today.",
        deduplication_key=dedup_key,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    )
    assert n2.id == n1.id
    assert len(notif_setup["mock_email"].sent_messages) == initial_email_count


@pytest.mark.asyncio
async def test_admin_broadcast_announcement(client: AsyncClient, notif_setup, db_session: AsyncSession):
    """Tests administrative announcement broadcasting to active students with audit logging."""
    admin_headers = {"Authorization": f"Bearer {notif_setup['admin_token']}"}

    res = await client.post(
        "/api/v1/notifications/broadcast",
        headers=admin_headers,
        json={
            "title": "Platform Scheduled Maintenance",
            "body": "System update scheduled for 2:00 AM UTC.",
            "type": "SYSTEM_NOTICE",
            "channels": ["IN_APP"],
            "target_role": "STUDENT",
        },
    )
    assert res.status_code == 200
    b_data = res.json()
    assert b_data["success"] is True
    assert b_data["dispatched_notifications"] >= 1

    # Verify audit log was recorded
    stmt = select(AuditLog).where(AuditLog.action == "admin.broadcast_notification")
    audit_res = await db_session.execute(stmt)
    assert audit_res.scalars().first() is not None
