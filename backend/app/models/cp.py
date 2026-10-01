"""Phase 8: Competitive Programming domain models.

Provides models for:
- Competitive Programming Problem Metadata (rating band, limits, I/O formats, constraints)
- Competitive Rating (separate from practice rating)
- Competitive Rating History audit trail
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.content import Problem
    from backend.app.models.user import User


class CPProblemMetadata(Base):
    """Competitive programming metadata associated with a core Problem."""

    __tablename__ = "cp_problem_metadata"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    rating_band: Mapped[int] = mapped_column(
        Integer, default=1200, nullable=False, index=True
    )  # e.g. 800, 1000.. 2400
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)

    input_format: Mapped[str] = mapped_column(Text, default="", nullable=False)
    output_format: Mapped[str] = mapped_column(Text, default="", nullable=False)
    constraints: Mapped[str] = mapped_column(Text, default="", nullable=False)
    editorial: Mapped[str | None] = mapped_column(Text, nullable=True)

    problem: Mapped["Problem"] = relationship("Problem")


class CompetitiveRating(Base):
    """Separate competitive programming rating distinct from Phase 7 practice rating."""

    __tablename__ = "competitive_ratings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    current_rating: Mapped[int] = mapped_column(
        Integer, default=1200, nullable=False, index=True
    )
    peak_rating: Mapped[int] = mapped_column(Integer, default=1200, nullable=False)
    contests_played: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contests_won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    problems_solved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")


class CompetitiveRatingHistory(Base):
    """Immutable audit trail for competitive programming rating adjustments."""

    __tablename__ = "competitive_rating_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    previous_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    new_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # CONTEST, CP_SOLVE, RATING_UPDATE
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User")

    __table_args__ = (Index("ix_cp_rating_hist_user_created", "user_id", "created_at"),)
