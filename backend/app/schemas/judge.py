"""Pydantic schemas for Phase 5 Online Judge API."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict

from backend.app.models.judge import JudgeJobStatus, Verdict


class SubmissionResultRead(BaseModel):
    """Execution outcome for a judged code submission."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    verdict: Verdict
    tests_total: int
    tests_passed: int
    execution_time_ms: Optional[int] = None
    memory_used_bytes: Optional[int] = None
    compiler_output_safe: Optional[str] = None
    runtime_output_safe: Optional[str] = None
    created_at: datetime


class JudgeJobRead(BaseModel):
    """Queue processing state of an asynchronous judge job."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    status: JudgeJobStatus
    attempt_count: int
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JudgeHealthRead(BaseModel):
    """Diagnostic health status for admin monitoring."""
    queue: Dict[str, Any]
    sandbox: Dict[str, Any]
