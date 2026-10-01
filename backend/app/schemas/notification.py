"""Pydantic schemas for Notifications and Notification Preferences."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.notification import NotificationType, NotificationChannel


class NotificationItem(BaseModel):
    """User notification display item."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    data_json: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated list of notifications with global unread counter."""
    items: List[NotificationItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Quick unread notification count badge response."""
    unread_count: int


class NotificationPreferenceItem(BaseModel):
    """Single channel/type preference entry."""
    model_config = ConfigDict(from_attributes=True)

    channel: NotificationChannel
    notification_type: NotificationType
    is_enabled: bool


class NotificationPreferencesResponse(BaseModel):
    """All notification preferences for the current authenticated user."""
    preferences: List[NotificationPreferenceItem]


class UpdatePreferenceItem(BaseModel):
    """Update payload for a single preference toggle."""
    channel: NotificationChannel
    notification_type: NotificationType
    is_enabled: bool


class UpdateNotificationPreferencesRequest(BaseModel):
    """Bulk update payload for user notification preferences."""
    preferences: List[UpdatePreferenceItem]


class AdminBroadcastRequest(BaseModel):
    """Admin payload to dispatch a system-wide or targeted notification."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=128, description="Announcement title")
    body: str = Field(..., min_length=5, max_length=2000, description="Announcement body")
    type: NotificationType = Field(default=NotificationType.SYSTEM_NOTICE)
    channels: List[NotificationChannel] = Field(default=[NotificationChannel.IN_APP])
    target_role: Optional[str] = Field(default=None, description="Optional target role filter (e.g. STUDENT)")
    target_plan: Optional[str] = Field(default=None, description="Optional target plan filter (e.g. PREMIUM)")
    action_url: Optional[str] = Field(default=None, max_length=255, description="Optional CTA hyperlink")


class AdminBroadcastResponse(BaseModel):
    """Result of administrative broadcast operation."""
    success: bool
    recipient_count: int
    dispatched_notifications: int
    broadcast_id: str
    channels: List[NotificationChannel]
