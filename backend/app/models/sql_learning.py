"""Phase 8: SQL Learning and Practice Engine domain models.

Provides models for:
- SQL Problems (DDL schema, seed data, reference solution query, allowed features, order sensitivity)
- SQL Submissions and execution audit records
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.user import User


class SQLProblem(Base):
    """SQL Practice Problem with isolated sandbox test definition."""

    __tablename__ = "sql_problems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    difficulty: Mapped[str] = mapped_column(
        String(32), default="MEDIUM", nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(64), default="BASICS", nullable=False, index=True
    )

    # Sandbox environment initialization scripts
    schema_ddl: Mapped[str] = mapped_column(Text, nullable=False)
    seed_data_sql: Mapped[str] = mapped_column(Text, nullable=False)
    solution_sql: Mapped[str] = mapped_column(Text, nullable=False)

    is_order_sensitive: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    allowed_features: Mapped[str | None] = mapped_column(String(255), nullable=True)
    time_limit_seconds: Mapped[float] = mapped_column(
        Float, default=3.0, nullable=False
    )

    access_level: Mapped[str] = mapped_column(
        String(32), default="FREE", nullable=False
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
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


class SQLSubmission(Base):
    """SQL Query evaluation attempt executed inside isolated sandbox."""

    __tablename__ = "sql_submissions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sql_problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sql_problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    query: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # ACCEPTED, WRONG_ANSWER, SYNTAX_ERROR, FORBIDDEN_KEYWORD, TIME_LIMIT_EXCEEDED, SYSTEM_ERROR
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User")
    sql_problem: Mapped["SQLProblem"] = relationship("SQLProblem")

    __table_args__ = (
        Index("ix_sql_submissions_user_problem", "user_id", "sql_problem_id"),
    )
