"""Security and administrative audit trail database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AuditLog(Base):
    """Immutable audit trail for security-critical actions and administrative events."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="User ID of actor or 'anonymous' / 'system'",
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="e.g. auth.login, auth.register, payment.order_created, premium.activated",
    )
    target_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    target_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Sanitized contextual metadata (secrets strictly scrubbed)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
