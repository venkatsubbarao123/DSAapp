"""Phase 8: Contest System domain models.

Provides models for:
- Contests (DRAFT, UPCOMING, LIVE, ENDED, ARCHIVED)
- Contest Problems and Points/Penalties
- Contest Participants
- Contest Submissions
- Contest Anti-Cheat Signals
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.content import Problem
    from backend.app.models.progress import Submission


class ContestStatus(str, enum.Enum):
    """Lifecycle states of a contest."""
    DRAFT = "DRAFT"
    UPCOMING = "UPCOMING"
    LIVE = "LIVE"
    ENDED = "ENDED"
    ARCHIVED = "ARCHIVED"


class ContestVisibility(str, enum.Enum):
    """Contest visibility."""
    PUBLIC = "PUBLIC"
    UNLISTED = "UNLISTED"
    PRIVATE = "PRIVATE"


class Contest(Base):
    """Contest event model."""
    __tablename__ = "contests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[ContestStatus] = mapped_column(String(32), default=ContestStatus.DRAFT, nullable=False, index=True)

    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g. 7200 (2 hrs)

    visibility: Mapped[str] = mapped_column(String(32), default=ContestVisibility.PUBLIC.value, nullable=False)
    premium_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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

    # Relationships
    problems: Mapped[List["ContestProblem"]] = relationship(
        "ContestProblem",
        back_populates="contest",
        cascade="all, delete-orphan",
        order_by="ContestProblem.sequence",
    )
    participants: Mapped[List["ContestParticipant"]] = relationship(
        "ContestParticipant",
        back_populates="contest",
        cascade="all, delete-orphan",
    )
    submissions: Mapped[List["ContestSubmission"]] = relationship(
        "ContestSubmission",
        back_populates="contest",
        cascade="all, delete-orphan",
    )

    def compute_dynamic_status(self) -> ContestStatus:
        """Determines server-authoritative status based on UTC current time."""
        if self.status in (ContestStatus.DRAFT, ContestStatus.ARCHIVED):
            return ContestStatus(self.status)
        now_utc = datetime.now(timezone.utc)
        start = self.start_at if self.start_at.tzinfo else self.start_at.replace(tzinfo=timezone.utc)
        end = self.end_at if self.end_at.tzinfo else self.end_at.replace(tzinfo=timezone.utc)
        if now_utc < start:
            return ContestStatus.UPCOMING
        elif start <= now_utc < end:
            return ContestStatus.LIVE
        else:
            return ContestStatus.ENDED

    @property
    def remaining_seconds(self) -> int:
        """Server-authoritative remaining time in seconds."""
        now_utc = datetime.now(timezone.utc)
        start = self.start_at if self.start_at.tzinfo else self.start_at.replace(tzinfo=timezone.utc)
        end = self.end_at if self.end_at.tzinfo else self.end_at.replace(tzinfo=timezone.utc)
        if now_utc >= end:
            return 0
        if now_utc < start:
            return self.duration_seconds
        return max(0, int((end - now_utc).total_seconds()))


class ContestProblem(Base):
    """Problem included in a contest with assigned sequence and points."""
    __tablename__ = "contest_problems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contest_id: Mapped[str] = mapped_column(String(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)

    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    penalty_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    difficulty: Mapped[str] = mapped_column(String(32), default="MEDIUM", nullable=False)

    contest: Mapped["Contest"] = relationship("Contest", back_populates="problems")
    problem: Mapped["Problem"] = relationship("Problem")

    __table_args__ = (
        UniqueConstraint("contest_id", "problem_id", name="uq_contest_problem"),
        UniqueConstraint("contest_id", "sequence", name="uq_contest_sequence"),
        Index("ix_contest_problems_contest_seq", "contest_id", "sequence"),
    )


class ContestParticipant(Base):
    """Contest registration and participant performance record."""
    __tablename__ = "contest_participants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contest_id: Mapped[str] = mapped_column(String(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    final_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    final_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    contest: Mapped["Contest"] = relationship("Contest", back_populates="participants")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("contest_id", "user_id", name="uq_contest_user"),
        Index("ix_contest_participants_score", "contest_id", "final_score", "final_penalty"),
    )


class ContestSubmission(Base):
    """Link between a contest and a student's code submission."""
    __tablename__ = "contest_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contest_id: Mapped[str] = mapped_column(String(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True)
    participant_id: Mapped[str] = mapped_column(String(36), ForeignKey("contest_participants.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True)
    submission_id: Mapped[str] = mapped_column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True)

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    verdict: Mapped[str] = mapped_column(String(64), default="QUEUED", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    penalty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    contest: Mapped["Contest"] = relationship("Contest", back_populates="submissions")
    participant: Mapped["ContestParticipant"] = relationship("ContestParticipant")
    problem: Mapped["Problem"] = relationship("Problem")
    submission: Mapped["Submission"] = relationship("Submission")

    __table_args__ = (
        Index("ix_contest_submissions_contest_prob", "contest_id", "problem_id"),
        Index("ix_contest_submissions_participant", "participant_id"),
    )


class ContestCheatSignal(Base):
    """Application-level anti-cheat signal audit record."""
    __tablename__ = "contest_cheat_signals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contest_id: Mapped[str] = mapped_column(String(36), ForeignKey("contests.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)  # RAPID_SUBMISSIONS, REPEATED_CODE, etc.
    details_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    contest: Mapped["Contest"] = relationship("Contest")
    user: Mapped["User"] = relationship("User")
