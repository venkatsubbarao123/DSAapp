"""Phase 8: Interview Mode domain models.

Provides models for:
- Interview Sessions (General Software, DSA, Python, Java, SQL, OOP, Mixed Technical)
- Interview Questions (MCQ, CODING, SQL, OOP, DEBUGGING, CONCEPTUAL)
- Server-authoritative timing, completion, and evaluation records.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
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
    from backend.app.models.user import User


class InterviewMode(str, enum.Enum):
    """Supported technical interview simulation tracks."""

    GENERAL_SOFTWARE = "GENERAL_SOFTWARE"
    DSA = "DSA"
    PYTHON = "PYTHON"
    JAVA = "JAVA"
    SQL = "SQL"
    OOP = "OOP"
    MIXED_TECHNICAL = "MIXED_TECHNICAL"


class InterviewStatus(str, enum.Enum):
    """Lifecycle state of an interview simulation session."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    EXPIRED = "EXPIRED"


class InterviewSession(Base):
    """Simulated interview session container."""

    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(32),
        default=InterviewMode.GENERAL_SOFTWARE.value,
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=InterviewStatus.IN_PROGRESS.value,
        nullable=False,
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer, default=2700, nullable=False
    )  # 45 minutes

    total_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    answered_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluation_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING, EVALUATED, FAILED

    # Detailed feedback: score by category, time management, areas to improve, recommended topics
    feedback_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)

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
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.sequence",
    )

    @property
    def remaining_seconds(self) -> int:
        """Server-authoritative remaining time in seconds."""
        if self.status != InterviewStatus.IN_PROGRESS.value:
            return 0
        now_utc = datetime.now(timezone.utc)
        started = (
            self.started_at
            if self.started_at.tzinfo
            else self.started_at.replace(tzinfo=timezone.utc)
        )
        elapsed = int((now_utc - started).total_seconds())
        return max(0, self.duration_seconds - elapsed)

    @property
    def is_expired(self) -> bool:
        """Whether session has exceeded duration."""
        return self.remaining_seconds <= 0

    __table_args__ = (Index("ix_interview_sessions_user_status", "user_id", "status"),)


class InterviewQuestion(Base):
    """Individual question asked during an interview simulation."""

    __tablename__ = "interview_questions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # MCQ, CODING, SQL, OOP, DEBUGGING, CONCEPTUAL
    question_title: Mapped[str] = mapped_column(String(255), nullable=False)
    question_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    options: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )  # List of choices for MCQ
    correct_option: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # Protected; not exposed to student
    difficulty: Mapped[str] = mapped_column(
        String(32), default="MEDIUM", nullable=False
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evaluation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    session: Mapped["InterviewSession"] = relationship(
        "InterviewSession", back_populates="questions"
    )

    __table_args__ = (
        Index("ix_interview_questions_session_seq", "session_id", "sequence"),
    )
