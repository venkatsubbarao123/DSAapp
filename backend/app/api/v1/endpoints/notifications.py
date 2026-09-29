"""Endpoints for user notifications, read states, channel preferences, and admin broadcasts."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Request, status

from backend.app.api.deps import (
    get_current_user,
    get_notification_service,
    require_admin,
)
from backend.app.models.user import User
from backend.app.schemas.notification import (
    AdminBroadcastRequest,
    AdminBroadcastResponse,
    NotificationItem,
    NotificationListResponse,
    NotificationPreferencesResponse,
    UnreadCountResponse,
    UpdateNotificationPreferencesRequest,
)
from backend.app.services.notification.notification_service import NotificationService

router = APIRouter()


# =============================================================================
# USER NOTIFICATIONS
# =============================================================================

@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Retrieves paginated notifications for the authenticated user."""
    return await notification_service.list_user_notifications(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Fast unread notification count badge for the top navigation bar."""
    count = await notification_service.get_unread_count(user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationItem)
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Marks a single notification as read."""
    return await notification_service.mark_as_read(
        user_id=current_user.id,
        notification_id=notification_id,
    )


@router.post("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Marks all unread notifications for the authenticated user as read."""
    marked = await notification_service.mark_all_as_read(user_id=current_user.id)
    return {"success": True, "marked_count": marked}


# =============================================================================
# PREFERENCES
# =============================================================================

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Retrieves full channel and event type preferences matrix for the authenticated user."""
    return await notification_service.get_user_preferences(user_id=current_user.id)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    payload: UpdateNotificationPreferencesRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Updates one or more notification channel toggles."""
    return await notification_service.update_user_preferences(
        user_id=current_user.id,
        request=payload,
    )


# =============================================================================
# ADMIN BROADCAST
# =============================================================================

@router.post("/broadcast", response_model=AdminBroadcastResponse)
async def broadcast_notification(
    payload: AdminBroadcastRequest,
    request: Request,
    current_user: User = Depends(require_admin),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Admin-only: Broadcasts announcement across in-app and email channels to targeted learners."""
    ip_addr = request.client.host if request.client else None
    return await notification_service.broadcast_notification(
        admin_user=current_user,
        request=payload,
        ip_address=ip_addr,
    )
