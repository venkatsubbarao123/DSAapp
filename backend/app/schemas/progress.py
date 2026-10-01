"""Pydantic schemas for progress tracking, submissions, mistakes notebook, and spaced revision."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.progress import (
    LessonProgressStatus,
    MistakeType,
    ProblemProgressStatus,
    ReviewOutcome,
    RevisionScheduleStatus,
    RevisionSourceType,
    SubmissionStatus,
)

ALLOWED_LANGUAGES = {"python", "javascript", "typescript", "java", "cpp"}
MAX_SOURCE_CODE_BYTES = 64 * 1024  # 64 KB


# ---------------------------------------------------------------------------
# Progress Schemas
# ---------------------------------------------------------------------------

class UserLessonProgressRead(BaseModel):
    """Lesson progress detail schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    lesson_id: str
    status: LessonProgressStatus
    progress_percent: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_viewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserProblemProgressRead(BaseModel):
    """Problem progress detail schema."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    problem_id: str
    status: ProblemProgressStatus
    attempts_count: int
    successful_attempts: int
    first_attempted_at: Optional[datetime] = None
    last_attempted_at: Optional[datetime] = None
    solved_at: Optional[datetime] = None
    bookmarked: bool
    personal_difficulty: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ProgressActivityItem(BaseModel):
    """Recent learner activity event."""
    title: str
    entity_type: str  # "LESSON" or "PROBLEM"
    slug: str
    status: str
    timestamp: datetime


class ProgressOverviewRead(BaseModel):
    """High-level learner progress overview calculated from real database state."""
    lessons_started: int
    lessons_completed: int
    total_visible_lessons: int
    lesson_completion_percent: float

    problems_attempted: int
    problems_solved: int
    total_visible_problems: int
    problem_solving_percent: float

    overall_completion_percent: float
    recent_activity: List[ProgressActivityItem]
    due_revisions_count: int
    unresolved_mistakes_count: int


class TopicProgressRead(BaseModel):
    """Aggregated topic completion metrics."""
    topic_id: str
    topic_title: str
    topic_slug: str
    total_lessons: int
    completed_lessons: int
    total_problems: int
    solved_problems: int
    completion_percent: float


class MasteryInsightsRead(BaseModel):
    """Premium-tier mastery metrics and learning retention forecasting."""
    spaced_retention_score: float
    streak_days: int
    mistake_breakdown: Dict[str, int]
    pattern_mastery: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Submission Schemas
# ---------------------------------------------------------------------------

class SubmissionCreate(BaseModel):
    """Client submission payload.

    CRITICAL: Strict language allowlist and 64KB UTF-8 source limit.
    """
    model_config = ConfigDict(extra="forbid")

    problem_id: str = Field(..., min_length=1, max_length=64)
    language: str = Field(..., min_length=1, max_length=32)
    source_code: str = Field(..., min_length=1)
    idempotency_key: Optional[str] = Field(None, max_length=128)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        lang = v.strip().lower()
        if lang not in ALLOWED_LANGUAGES:
            raise ValueError(f"Unsupported language '{v}'. Allowed: {sorted(list(ALLOWED_LANGUAGES))}")
        return lang

    @field_validator("source_code")
    @classmethod
    def validate_source_code(cls, v: str) -> str:
        encoded = v.encode("utf-8")
        if len(encoded) > MAX_SOURCE_CODE_BYTES:
            raise ValueError(f"Source code exceeds maximum allowed size of {MAX_SOURCE_CODE_BYTES} bytes (64 KB).")
        if not v.strip():
            raise ValueError("Source code cannot be empty.")
        return v


class SubmissionSummary(BaseModel):
    """Summary item for submission history listing. (Ommits source code for privacy/performance)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_id: str
    problem_id: str
    problem_title: str
    problem_slug: str
    language: str
    status: SubmissionStatus
    created_at: datetime
    execution_notice: str = "Code recorded securely. Future online judge execution will evaluate in Phase 7."
    result: Optional[Any] = None


class SubmissionDetail(BaseModel):
    """Full submission detail containing source code (Strictly Owner-Only)."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_id: str
    problem_id: str
    problem_title: str
    problem_slug: str
    language: str
    source_code: str
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime
    execution_notice: str = "Code recorded securely. Future online judge execution will evaluate in Phase 7."
    result: Optional[Any] = None


# ---------------------------------------------------------------------------
# Mistake Notebook Schemas
# ---------------------------------------------------------------------------

class MistakeCreate(BaseModel):
    """Create mistake entry in learner's notebook."""
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=10000)
    correction: Optional[str] = Field(None, max_length=10000)
    mistake_type: MistakeType
    problem_id: Optional[str] = Field(None, max_length=64)
    lesson_id: Optional[str] = Field(None, max_length=64)


class MistakeUpdate(BaseModel):
    """Update mistake entry."""
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=10000)
    correction: Optional[str] = Field(None, max_length=10000)
    mistake_type: Optional[MistakeType] = None
    is_resolved: Optional[bool] = None


class MistakeRead(BaseModel):
    """Mistake notebook record."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_id: str
    user_id: str
    problem_id: Optional[str] = None
    problem_title: Optional[str] = None
    problem_slug: Optional[str] = None
    lesson_id: Optional[str] = None
    lesson_title: Optional[str] = None
    lesson_slug: Optional[str] = None
    mistake_type: MistakeType
    title: str
    description: str
    correction: Optional[str] = None
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Spaced Revision Schemas
# ---------------------------------------------------------------------------

class RevisionItemCreate(BaseModel):
    """Create revision item queue entry."""
    model_config = ConfigDict(extra="forbid")

    source_type: RevisionSourceType
    source_id: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=255)
    priority: int = Field(1, ge=1, le=3)


class ReviewActionRequest(BaseModel):
    """Learner self-assessment on review."""
    model_config = ConfigDict(extra="forbid")

    outcome: ReviewOutcome


class RevisionScheduleRead(BaseModel):
    """Revision schedule details."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    due_at: datetime
    last_reviewed_at: Optional[datetime] = None
    review_count: int
    interval_days: float
    ease_factor: float
    status: RevisionScheduleStatus


class RevisionItemRead(BaseModel):
    """Revision item with schedule."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    public_id: str
    source_type: RevisionSourceType
    source_id: str
    title: str
    priority: int
    is_active: bool
    schedule: Optional[RevisionScheduleRead] = None
    created_at: datetime
    is_overdue: bool = False
    is_due_now: bool = False
