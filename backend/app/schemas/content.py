"""Pydantic v2 schemas for Curriculum, Topics, Lessons, and Problems."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
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
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


# --- Lesson Content Structured Block ---

class LessonBlock(BaseModel):
    """Structured, safe educational content block (XSS immune, no raw HTML)."""
    type: str = Field(..., description="Block type: heading, paragraph, code, note, tip, warning, example, table")
    content: str
    level: Optional[int] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


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
    explanation: Optional[str] = None
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
    short_description: Optional[str] = None
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
    tracks: List[TrackSummary] = []
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
    track_id: Optional[str] = None
    slug: str
    title: str
    description: str
    display_order: int
    difficulty: ContentLevel
    access_level: ContentAccessLevel
    status: ContentStatus


class TopicDetail(TopicSummary):
    subtopics: List[SubtopicSummary] = []
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
    blocks: List[LessonBlock] = []
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
    topic_id: Optional[str] = None
    subtopic_id: Optional[str] = None
    display_order: int
    estimated_minutes: int
    tags: List[TagResponse] = []
    patterns: List[PatternResponse] = []


class ProblemDetail(BaseModel):
    """Complete problem specification for students."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    public_id: str
    slug: str
    title: str
    statement: str
    explanation: Optional[str] = None
    difficulty: ProblemDifficulty
    access_level: ContentAccessLevel
    status: ContentStatus
    topic_id: Optional[str] = None
    subtopic_id: Optional[str] = None
    display_order: int
    estimated_minutes: int
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    expected_time_complexity: Optional[str] = None
    expected_space_complexity: Optional[str] = None
    supported_languages: List[str] = []
    version: int
    examples: List[ProblemExampleResponse] = []
    hints: List[HintResponse] = []
    sample_test_cases: List[TestCaseResponse] = []
    tags: List[TagResponse] = []
    patterns: List[PatternResponse] = []
    created_at: datetime
    updated_at: datetime


# --- Admin / Content Editor Management Schemas (Strict Extra Forbid) ---

class CurriculumCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    short_description: Optional[str] = None
    level: ContentLevel = ContentLevel.BEGINNER
    display_order: int = 0
    is_free: bool = True


class TopicCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    description: str
    track_id: Optional[str] = None
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
    blocks: List[LessonBlock]
    estimated_minutes: int = 15
    difficulty: ContentLevel = ContentLevel.BEGINNER
    display_order: int = 0
    access_level: ContentAccessLevel = ContentAccessLevel.FREE


class ProblemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str = Field(..., min_length=2, max_length=128)
    title: str = Field(..., min_length=3, max_length=255)
    statement: str
    explanation: Optional[str] = None
    difficulty: ProblemDifficulty = ProblemDifficulty.EASY
    access_level: ContentAccessLevel = ContentAccessLevel.FREE
    topic_id: Optional[str] = None
    subtopic_id: Optional[str] = None
    display_order: int = 0
    estimated_minutes: int = 25
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    constraints: Optional[str] = None
    expected_time_complexity: Optional[str] = None
    expected_space_complexity: Optional[str] = None
    supported_languages: List[str] = ["python", "java", "cpp", "javascript"]
    tag_names: List[str] = []
    pattern_names: List[str] = []


class ContentStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: ContentStatus
