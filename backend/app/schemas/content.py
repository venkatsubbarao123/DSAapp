"""Pydantic v2 schemas for Curriculum, Topics, Lessons, and Problems."""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ContentStatus,
    ProblemDifficulty,
)

T = TypeVar("T")


# --- Pagination Envelope ---


class PaginatedData(BaseModel, Generic[T]):
    """Standardized pagination structure matching DSAapp API specifications."""

    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


# --- Lesson Content Structured Block ---


class LessonBlock(BaseModel):
    """Structured, safe educational content block (XSS immune, no raw HTML)."""

    type: str = Field(
        ...,
        description="Block type: heading, paragraph, code, note, tip, warning, example, table",
    )
    content: str
    level: int | None = None
    language: str | None = None
    metadata: dict[str, Any] | None = None


# --- Shared Auxiliary Schemas ---


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    slug: str
    name: str


class PatternResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    slug: str
    name: str
    description: str


class ProblemExampleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    input: str
    output: str
    explanation: str | None = None
    display_order: int


class HintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    hint_number: int
    title: str
    content: str
    is_premium: bool


class TestCaseResponse(BaseModel):
    """Safe test case representation for students (SAMPLE ONLY).

    SECURITY INVARIANT:
    Hidden test cases (is_hidden == True) are NEVER returned through this schema.
    """

    model_config = ConfigDict(from_attributes=True)
    id: str
    input: str
    expected_output: str
    is_sample: bool
    display_order: int


# --- Curriculum & Track Schemas ---


class CurriculumSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    slug: str
    title: str
    short_description: str | None = None
    level: ContentLevel
    status: ContentStatus
    display_order: int
    is_free: bool


class TrackSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    curriculum_id: str
    slug: str
    title: str
    description: str
    level: ContentLevel
    display_order: int
    status: ContentStatus
    access_level: ContentAccessLevel


class CurriculumDetail(CurriculumSummary):
    description: str
    tracks: list[TrackSummary] = []
    created_at: datetime
    updated_at: datetime


# --- Topic & Subtopic Schemas ---


class SubtopicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    topic_id: str
    slug: str
    title: str
    description: str
    display_order: int
    difficulty: ContentLevel
    access_level: ContentAccessLevel
    status: ContentStatus


class TopicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    track_id: str | None = None
    slug: str
    title: str
    description: str
    display_order: int
    difficulty: ContentLevel
    access_level: ContentAccessLevel
    status: ContentStatus


class TopicDetail(TopicSummary):
    subtopics: list[SubtopicSummary] = []
    created_at: datetime
    updated_at: datetime


class SubtopicDetail(SubtopicSummary):
    lessons_count: int = 0
    problems_count: int = 0
    created_at: datetime
    updated_at: datetime


# --- Lesson Schemas ---


class LessonSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    subtopic_id: str
    slug: str
    title: str
    summary: str
    estimated_minutes: int
    difficulty: ContentLevel
    display_order: int
    access_level: ContentAccessLevel
    status: ContentStatus
    version: int


class LessonDetail(LessonSummary):
    blocks: list[LessonBlock] = []
    created_at: datetime
    updated_at: datetime


# --- Problem Schemas ---


class ProblemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    slug: str
    title: str
    difficulty: ProblemDifficulty
    access_level: ContentAccessLevel
    status: ContentStatus
    topic_id: str | None = None
    subtopic_id: str | None = None
    display_order: int
    estimated_minutes: int
    tags: list[TagResponse] = []
    patterns: list[PatternResponse] = []


class ProblemDetail(BaseModel):
    """Complete problem specification for students."""

    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    slug: str
    title: str
    statement: str
    explanation: str | None = None
    difficulty: ProblemDifficulty
    access_level: ContentAccessLevel
    status: ContentStatus
    topic_id: str | None = None
    subtopic_id: str | None = None
    display_order: int
    estimated_minutes: int
    input_format: str | None = None
    output_format: str | None = None
    constraints: str | None = None
    expected_time_complexity: str | None = None
    expected_space_complexity: str | None = None
    supported_languages: list[str] = []
    version: int
    examples: list[ProblemExampleResponse] = []
    hints: list[HintResponse] = []
    sample_test_cases: list[TestCaseResponse] = []
    tags: list[TagResponse] = []
    patterns: list[PatternResponse] = []
    created_at: datetime
    updated_at: datetime


# --- Admin / Content Editor Management Schemas (Strict Extra Forbid) ---


class CurriculumCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    short_description: str | None = None
    level: ContentLevel = ContentLevel.BEGINNER
    display_order: int = 0
    is_free: bool = True


class TopicCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    track_id: str | None = None
    display_order: int = 0
    difficulty: ContentLevel = ContentLevel.BEGINNER
    access_level: ContentAccessLevel = ContentAccessLevel.FREE


class SubtopicCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic_id: str
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    display_order: int = 0
    difficulty: ContentLevel = ContentLevel.BEGINNER
    access_level: ContentAccessLevel = ContentAccessLevel.FREE


class LessonCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subtopic_id: str
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    summary: str
    blocks: list[LessonBlock]
    estimated_minutes: int = 15
    difficulty: ContentLevel = ContentLevel.BEGINNER
    display_order: int = 0
    access_level: ContentAccessLevel = ContentAccessLevel.FREE


class ProblemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    statement: str
    explanation: str | None = None
    difficulty: ProblemDifficulty = ProblemDifficulty.EASY
    access_level: ContentAccessLevel = ContentAccessLevel.FREE
    topic_id: str | None = None
    subtopic_id: str | None = None
    display_order: int = 0
    estimated_minutes: int = 25
    input_format: str | None = None
    output_format: str | None = None
    constraints: str | None = None
    expected_time_complexity: str | None = None
    expected_space_complexity: str | None = None
    supported_languages: list[str] = ["python", "java", "cpp", "javascript"]
    tag_names: list[str] = []
    pattern_names: list[str] = []


class ContentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ContentStatus
