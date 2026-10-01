"""Pydantic schemas for Phase 8 SQL Learning & Practice Engine."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SQLProblemSummary(BaseModel):
    """Listing summary for SQL practice problems."""

    id: str
    title: str
    slug: str
    difficulty: str
    category: str
    is_order_sensitive: bool
    access_level: str
    solved: bool = False


class SQLProblemDetail(BaseModel):
    """Detailed SQL problem statement with database schema and sample data."""

    id: str
    title: str
    slug: str
    description: str
    difficulty: str
    category: str
    schema_ddl: str
    sample_data_sql: str
    is_order_sensitive: bool
    allowed_features: str | None = None
    access_level: str
    solved: bool = False


class RunSQLQueryRequest(BaseModel):
    """Dry-run SQL query execution request against isolated sandbox."""

    query: str = Field(..., max_length=16384)


class RunSQLQueryResponse(BaseModel):
    """Dry-run execution output from isolated SQLite sandbox."""

    verdict: str  # SUCCESS, SYNTAX_ERROR, FORBIDDEN_KEYWORD, TIME_LIMIT_EXCEEDED
    execution_time_ms: float
    columns: list[str] = []
    rows: list[list[Any]] = []
    error_message: str | None = None


class SubmitSQLQueryRequest(BaseModel):
    """Authoritative SQL query submission for evaluation against test suites."""

    query: str = Field(..., max_length=16384)


class SubmitSQLQueryResponse(BaseModel):
    """Evaluation verdict of student SQL query."""

    submission_id: str
    verdict: str  # ACCEPTED, WRONG_ANSWER, SYNTAX_ERROR, FORBIDDEN_KEYWORD, TIME_LIMIT_EXCEEDED, SYSTEM_ERROR
    execution_time_ms: float
    columns: list[str] = []
    rows: list[list[Any]] = []
    expected_columns: list[str] | None = None
    expected_rows_sample: list[list[Any]] | None = None
    error_message: str | None = None


class SQLSubmissionSummary(BaseModel):
    """Historical user submission record for an SQL problem."""

    id: str
    query: str
    verdict: str
    execution_time_ms: float
    error_message: str | None = None
    created_at: datetime
