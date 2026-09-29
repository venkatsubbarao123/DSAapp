"""Pydantic schemas for Phase 8 SQL Learning & Practice Engine."""

from datetime import datetime
from typing import Any, List, Optional
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
    allowed_features: Optional[str] = None
    access_level: str
    solved: bool = False


class RunSQLQueryRequest(BaseModel):
    """Dry-run SQL query execution request against isolated sandbox."""
    query: str = Field(..., max_length=16384)


class RunSQLQueryResponse(BaseModel):
    """Dry-run execution output from isolated SQLite sandbox."""
    verdict: str  # SUCCESS, SYNTAX_ERROR, FORBIDDEN_KEYWORD, TIME_LIMIT_EXCEEDED
    execution_time_ms: float
    columns: List[str] = []
    rows: List[List[Any]] = []
    error_message: Optional[str] = None


class SubmitSQLQueryRequest(BaseModel):
    """Authoritative SQL query submission for evaluation against test suites."""
    query: str = Field(..., max_length=16384)


class SubmitSQLQueryResponse(BaseModel):
    """Evaluation verdict of student SQL query."""
    submission_id: str
    verdict: str  # ACCEPTED, WRONG_ANSWER, SYNTAX_ERROR, FORBIDDEN_KEYWORD, TIME_LIMIT_EXCEEDED, SYSTEM_ERROR
    execution_time_ms: float
    columns: List[str] = []
    rows: List[List[Any]] = []
    expected_columns: Optional[List[str]] = None
    expected_rows_sample: Optional[List[List[Any]]] = None
    error_message: Optional[str] = None


class SQLSubmissionSummary(BaseModel):
    """Historical user submission record for an SQL problem."""
    id: str
    query: str
    verdict: str
    execution_time_ms: float
    error_message: Optional[str] = None
    created_at: datetime
