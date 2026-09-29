"""Notification domain models: In-App, Email delivery tracking, and user notification preferences."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class NotificationType(str, enum.Enum):
    """Categorical classification of notification events."""
    ACHIEVEMENT_UNLOCKED = "ACHIEVEMENT_UNLOCKED"
    DAILY_CHALLENGE = "DAILY_CHALLENGE"
    STREAK_REMINDER = "STREAK_REMINDER"
    REVISION_DUE = "REVISION_DUE"
    CONTEST_STARTING = "CONTEST_STARTING"
    CONTEST_RESULT = "CONTEST_RESULT"
    INTERVIEW_RESULT = "INTERVIEW_RESULT"
    PREMIUM_EXPIRING = "PREMIUM_EXPIRING"
    SYSTEM_NOTICE = "SYSTEM_NOTICE"


class NotificationChannel(str, enum.Enum):
    """Delivery transport channel."""
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"


class DeliveryStatus(str, enum.Enum):
    """Delivery lifecycle status."""
    QUEUED = "QUEUED"
    SENDING = "SENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notification(Base):
    """In-app persistent notification entity for learners."""
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Sanitized JSON metadata e.g. target URLs, entities",
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        "NotificationDelivery",
        back_populates="notification",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "read_at"),
        Index("idx_notifications_user_created", "user_id", "created_at"),
    )


class NotificationPreference(Base):
    """User-level notification channel and category opt-in preferences."""
    __tablename__ = "notification_preferences"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_challenge: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    streak_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    revision_reminders: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    contest_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    achievement_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    system_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])


class NotificationDelivery(Base):
    """Delivery log record for multi-channel transmission audit."""
    __tablename__ = "notification_deliveries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    notification_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel),
        nullable=False,
        index=True,
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus),
        default=DeliveryStatus.QUEUED,
        nullable=False,
        index=True,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    notification: Mapped["Notification"] = relationship("Notification", back_populates="deliveries")
