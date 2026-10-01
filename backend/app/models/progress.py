"""Progress, Submissions, Mistakes & Revision domain models."""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
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
    from backend.app.models.content import Problem, Lesson


class ProblemProgressStatus(str, enum.Enum):
    """User problem progress state."""
    NOT_STARTED = "NOT_STARTED"
    ATTEMPTED = "ATTEMPTED"
    SOLVED = "SOLVED"


class LessonProgressStatus(str, enum.Enum):
    """User lesson completion progress state."""
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class SubmissionStatus(str, enum.Enum):
    """Phase 5 Online Judge submission lifecycle states."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPILING = "COMPILING"
    JUDGING = "JUDGING"
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CANCELLED = "CANCELLED"
    # Backward compatibility with Phase 4 legacy records:
    QUEUED_FOR_FUTURE_JUDGE = "QUEUED_FOR_FUTURE_JUDGE"
    NOT_EXECUTED = "NOT_EXECUTED"


class MistakeType(str, enum.Enum):
    """Pedagogical classification of learner mistakes."""
    CONCEPT_GAP = "CONCEPT_GAP"
    LOGIC_ERROR = "LOGIC_ERROR"
    EDGE_CASE = "EDGE_CASE"
    COMPLEXITY_ISSUE = "COMPLEXITY_ISSUE"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    IMPLEMENTATION_ERROR = "IMPLEMENTATION_ERROR"
    MISUNDERSTANDING = "MISUNDERSTANDING"
    OTHER = "OTHER"


class RevisionSourceType(str, enum.Enum):
    """Target entity type scheduled for revision."""
    LESSON = "LESSON"
    PROBLEM = "PROBLEM"
    MISTAKE = "MISTAKE"


class RevisionScheduleStatus(str, enum.Enum):
    """Status of spaced revision cadence."""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class ReviewOutcome(str, enum.Enum):
    """Learner self-assessment feedback for spaced revision interval calculation."""
    AGAIN = "AGAIN"
    HARD = "HARD"
    GOOD = "GOOD"
    EASY = "EASY"


class UserProblemProgress(Base):
    """Per-user tracking of algorithmic problem engagement."""
    __tablename__ = "user_problem_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[ProblemProgressStatus] = mapped_column(
        Enum(ProblemProgressStatus),
        default=ProblemProgressStatus.NOT_STARTED,
        nullable=False,
    )
    attempts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    first_attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    bookmarked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    personal_difficulty: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

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

    user: Mapped["User"] = relationship("User", backref="problem_progress_records")
    problem: Mapped["Problem"] = relationship("Problem", backref="user_progress_records")

    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem_progress"),
        Index("ix_user_problem_progress_user_status", "user_id", "status"),
        Index("ix_user_problem_progress_user_updated", "user_id", "updated_at"),
        Index("ix_user_problem_progress_problem_id", "problem_id"),
    )


class UserLessonProgress(Base):
    """Per-user tracking of educational lesson reading and completion."""
    __tablename__ = "user_lesson_progress"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[str] = mapped_column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)

    status: Mapped[LessonProgressStatus] = mapped_column(
        Enum(LessonProgressStatus),
        default=LessonProgressStatus.NOT_STARTED,
        nullable=False,
    )
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_viewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    user: Mapped["User"] = relationship("User", backref="lesson_progress_records")
    lesson: Mapped["Lesson"] = relationship("Lesson", backref="user_progress_records")

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
        CheckConstraint("progress_percent >= 0 AND progress_percent <= 100", name="chk_lesson_progress_percent"),
        Index("ix_user_lesson_progress_user_status", "user_id", "status"),
        Index("ix_user_lesson_progress_user_updated", "user_id", "updated_at"),
        Index("ix_user_lesson_progress_lesson_id", "lesson_id"),
    )


class Submission(Base):
    """User code submission record for a problem."""
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: f"sub_{uuid.uuid4().hex[:12]}",
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[str] = mapped_column(String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False)

    language: Mapped[str] = mapped_column(String(32), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus),
        default=SubmissionStatus.QUEUED_FOR_FUTURE_JUDGE,
        nullable=False,
    )

    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

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

    user: Mapped["User"] = relationship("User", backref="user_submissions")
    problem: Mapped["Problem"] = relationship("Problem", backref="problem_submissions")

    __table_args__ = (
        Index("ix_submissions_user_created", "user_id", "created_at"),
        Index("ix_submissions_user_problem", "user_id", "problem_id"),
        Index("ix_submissions_user_status", "user_id", "status"),
        Index("ix_submissions_user_idempotency", "user_id", "idempotency_key"),
    )


class Mistake(Base):
    """Personal mistake notebook entry for conceptual or implementation bugs."""
    __tablename__ = "mistakes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: f"mst_{uuid.uuid4().hex[:12]}",
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    problem_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="SET NULL"),
        nullable=True,
    )
    lesson_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("lessons.id", ondelete="SET NULL"),
        nullable=True,
    )

    mistake_type: Mapped[MistakeType] = mapped_column(Enum(MistakeType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    correction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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

    user: Mapped["User"] = relationship("User", backref="user_mistakes")
    problem: Mapped[Optional["Problem"]] = relationship("Problem", backref="problem_mistakes")
    lesson: Mapped[Optional["Lesson"]] = relationship("Lesson", backref="lesson_mistakes")

    __table_args__ = (
        Index("ix_mistakes_user_resolved", "user_id", "is_resolved"),
        Index("ix_mistakes_user_type", "user_id", "mistake_type"),
        Index("ix_mistakes_user_created", "user_id", "created_at"),
    )


class RevisionItem(Base):
    """Spaced repetition item anchor referencing a lesson, problem, or mistake."""
    __tablename__ = "revision_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: f"rev_{uuid.uuid4().hex[:12]}",
        nullable=False,
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    source_type: Mapped[RevisionSourceType] = mapped_column(Enum(RevisionSourceType), nullable=False)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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

    user: Mapped["User"] = relationship("User", backref="user_revision_items")
    schedule: Mapped[Optional["RevisionSchedule"]] = relationship(
        "RevisionSchedule",
        back_populates="revision_item",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "source_type", "source_id", name="uq_user_revision_source"),
        Index("ix_revision_items_user_active", "user_id", "is_active"),
    )


class RevisionSchedule(Base):
    """Spaced repetition scheduling cadence metadata for a revision item."""
    __tablename__ = "revision_schedules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    revision_item_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("revision_items.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interval_days: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)

    status: Mapped[RevisionScheduleStatus] = mapped_column(
        Enum(RevisionScheduleStatus),
        default=RevisionScheduleStatus.ACTIVE,
        nullable=False,
    )

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

    revision_item: Mapped["RevisionItem"] = relationship("RevisionItem", back_populates="schedule")

    __table_args__ = (
        Index("ix_revision_schedules_due_at", "due_at"),
        Index("ix_revision_schedules_status_due", "status", "due_at"),
    )
