"""Pydantic schemas for Phase 5 Online Judge API."""

from datetime import datetime
from typing import Any

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
    execution_time_ms: int | None = None
    memory_used_bytes: int | None = None
    compiler_output_safe: str | None = None
    runtime_output_safe: str | None = None
    created_at: datetime


class JudgeJobRead(BaseModel):
    """Queue processing state of an asynchronous judge job."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    status: JudgeJobStatus
    attempt_count: int
    queued_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class JudgeHealthRead(BaseModel):
    """Diagnostic health status for admin monitoring."""

    queue: dict[str, Any]
    sandbox: dict[str, Any]


class RunCodeRequest(BaseModel):
    """Payload for executing code against sample test cases (non-persistent)."""

    language: str
    source_code: str
    custom_input: str | None = None


class TestCaseRunResult(BaseModel):
    """Result of running code against a single sample test case."""

    case_number: int
    input: str
    expected_output: str | None = None
    actual_output: str | None = None
    stderr: str | None = None
    passed: bool
    execution_time_ms: int
    status: str


class RunCodeResponse(BaseModel):
    """Aggregate response for sample code execution."""

    status: str
    all_passed: bool
    passed_count: int
    total_count: int
    peak_runtime_ms: int
    peak_memory_bytes: int
    compiler_output: str | None = None
    test_cases: list[TestCaseRunResult]
