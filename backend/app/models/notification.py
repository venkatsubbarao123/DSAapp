"""Notification domain models: In-App, Email delivery tracking, and user notification preferences."""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

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
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


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
    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Sanitized JSON metadata e.g. target URLs, entities",
    )
    read_at: Mapped[datetime | None] = mapped_column(
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

    def __init__(self, **kwargs):
        import json

        is_read = kwargs.pop("is_read", None)
        dedup_key = kwargs.pop("deduplication_key", None)
        data_json = kwargs.pop("data_json", None)
        if data_json and "metadata_json" not in kwargs:
            kwargs["metadata_json"] = data_json
        if dedup_key:
            meta = {}
            if kwargs.get("metadata_json"):
                try:
                    meta = json.loads(kwargs["metadata_json"])
                except Exception:
                    meta = {}
            meta["deduplication_key"] = dedup_key
            kwargs["metadata_json"] = json.dumps(meta)

        super().__init__(**kwargs)
        if is_read is not None:
            self.is_read = is_read

    @hybrid_property
    def is_read(self) -> bool:
        return self.read_at is not None

    @is_read.setter
    def is_read(self, val: bool) -> None:
        if val and self.read_at is None:
            self.read_at = datetime.now(timezone.utc)
        elif not val:
            self.read_at = None

    @is_read.expression
    def is_read(cls):
        return cls.read_at.isnot(None)

    @property
    def data_json(self) -> str | None:
        return self.metadata_json

    @property
    def deduplication_key(self) -> str | None:
        import json

        if not self.metadata_json:
            return None
        try:
            return json.loads(self.metadata_json).get("deduplication_key")
        except Exception:
            return None


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
    streak_reminders: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    revision_reminders: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    contest_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    achievement_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    system_notifications: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
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
    provider_message_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    notification: Mapped["Notification"] = relationship(
        "Notification", back_populates="deliveries"
    )
