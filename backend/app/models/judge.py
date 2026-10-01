"""Phase 5 Online Judge models: JudgeJob and SubmissionResult."""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.progress import Submission


class JudgeJobStatus(str, enum.Enum):
    """Execution state of a judge job."""
    QUEUED = "QUEUED"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY_PENDING = "RETRY_PENDING"
    CANCELLED = "CANCELLED"


class Verdict(str, enum.Enum):
    """Definitive judge verdicts for code submissions."""
    ACCEPTED = "ACCEPTED"
    WRONG_ANSWER = "WRONG_ANSWER"
    TIME_LIMIT_EXCEEDED = "TIME_LIMIT_EXCEEDED"
    MEMORY_LIMIT_EXCEEDED = "MEMORY_LIMIT_EXCEEDED"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    COMPILATION_ERROR = "COMPILATION_ERROR"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class JudgeJob(Base):
    """Durable job record for asynchronous online judging."""
    __tablename__ = "judge_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[JudgeJobStatus] = mapped_column(
        Enum(JudgeJobStatus),
        default=JudgeJobStatus.QUEUED,
        nullable=False,
        index=True,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)

    worker_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    queued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    submission: Mapped["Submission"] = relationship(
        "Submission",
        backref=backref("judge_job", lazy="selectin", uselist=False),
    )

    __table_args__ = (
        Index("ix_judge_jobs_status_queued_at", "status", "queued_at"),
        Index("ix_judge_jobs_heartbeat", "status", "heartbeat_at"),
    )


class SubmissionResult(Base):
    """Detailed execution result for a completed judge submission."""
    __tablename__ = "submission_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    verdict: Mapped[Verdict] = mapped_column(Enum(Verdict), nullable=False, index=True)
    tests_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_used_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Truncated safe outputs for diagnosis (max 4KB each)
    compiler_output_safe: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    runtime_output_safe: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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

    submission: Mapped["Submission"] = relationship(
        "Submission",
        backref=backref("result", lazy="selectin", uselist=False),
    )
