"""Content domain models: Curriculum, Track, Topic, Subtopic, Lesson, Concept, Problem, TestCase, Hints."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base


class ContentLevel(str, enum.Enum):
    """Pedagogical complexity level."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class ContentStatus(str, enum.Enum):
    """Publishing workflow states."""

    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ContentAccessLevel(str, enum.Enum):
    """Entitlement tier required to access content."""

    FREE = "FREE"
    PREMIUM = "PREMIUM"


class ProblemDifficulty(str, enum.Enum):
    """Standard problem difficulty classification."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"


# Many-to-Many Association: Problems <-> Tags
problem_tags = Table(
    "problem_tags",
    Base.metadata,
    Column(
        "problem_id",
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        String(36),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# Many-to-Many Association: Problems <-> Patterns
problem_patterns = Table(
    "problem_patterns",
    Base.metadata,
    Column(
        "problem_id",
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "pattern_id",
        String(36),
        ForeignKey("patterns.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Curriculum(Base):
    """Top-level curriculum organizing broad engineering domains."""

    __tablename__ = "curricula"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    public_id: Mapped[str] = mapped_column(
        String(36),
        default=lambda: f"cur_{uuid.uuid4().hex[:12]}",
        unique=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(512), nullable=True)
    level: Mapped[ContentLevel] = mapped_column(
        Enum(ContentLevel), default=ContentLevel.BEGINNER, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False, index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    tracks: Mapped[list["Track"]] = relationship(
        "Track",
        back_populates="curriculum",
        cascade="all, delete-orphan",
        order_by="Track.display_order",
    )


class Track(Base):
    """Learning tracks inside a curriculum (e.g. Core DSA, Interview Prep)."""

    __tablename__ = "tracks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    curriculum_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("curricula.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[ContentLevel] = mapped_column(
        Enum(ContentLevel), default=ContentLevel.BEGINNER, nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False, index=True
    )
    access_level: Mapped[ContentAccessLevel] = mapped_column(
        Enum(ContentAccessLevel), default=ContentAccessLevel.FREE, nullable=False
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

    curriculum: Mapped["Curriculum"] = relationship(
        "Curriculum", back_populates="tracks"
    )
    topics: Mapped[list["Topic"]] = relationship(
        "Topic",
        back_populates="track",
        cascade="all, delete-orphan",
        order_by="Topic.display_order",
    )


class Topic(Base):
    """Major DSA topics (e.g. Arrays, Trees, Dynamic Programming)."""

    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    public_id: Mapped[str] = mapped_column(
        String(36),
        default=lambda: f"top_{uuid.uuid4().hex[:12]}",
        unique=True,
        index=True,
    )
    track_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("tracks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difficulty: Mapped[ContentLevel] = mapped_column(
        Enum(ContentLevel), default=ContentLevel.BEGINNER, nullable=False
    )
    access_level: Mapped[ContentAccessLevel] = mapped_column(
        Enum(ContentAccessLevel), default=ContentAccessLevel.FREE, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False, index=True
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

    track: Mapped[Optional["Track"]] = relationship("Track", back_populates="topics")
    subtopics: Mapped[list["Subtopic"]] = relationship(
        "Subtopic",
        back_populates="topic",
        cascade="all, delete-orphan",
        order_by="Subtopic.display_order",
    )
    problems: Mapped[list["Problem"]] = relationship("Problem", back_populates="topic")


class Subtopic(Base):
    """Subtopics grouping granular lessons and problem subsets."""

    __tablename__ = "subtopics"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    topic_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difficulty: Mapped[ContentLevel] = mapped_column(
        Enum(ContentLevel), default=ContentLevel.BEGINNER, nullable=False
    )
    access_level: Mapped[ContentAccessLevel] = mapped_column(
        Enum(ContentAccessLevel), default=ContentAccessLevel.FREE, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False, index=True
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

    topic: Mapped["Topic"] = relationship("Topic", back_populates="subtopics")
    lessons: Mapped[list["Lesson"]] = relationship(
        "Lesson",
        back_populates="subtopic",
        cascade="all, delete-orphan",
        order_by="Lesson.display_order",
    )
    problems: Mapped[list["Problem"]] = relationship(
        "Problem", back_populates="subtopic"
    )

    __table_args__ = (
        Index("ix_subtopics_topic_slug", "topic_id", "slug", unique=True),
    )


class Lesson(Base):
    """Structured educational lesson unit."""

    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    public_id: Mapped[str] = mapped_column(
        String(36),
        default=lambda: f"les_{uuid.uuid4().hex[:12]}",
        unique=True,
        index=True,
    )
    subtopic_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("subtopics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    # Stored as serialized structured JSON blocks (never raw HTML)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    difficulty: Mapped[ContentLevel] = mapped_column(
        Enum(ContentLevel), default=ContentLevel.BEGINNER, nullable=False
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    access_level: Mapped[ContentAccessLevel] = mapped_column(
        Enum(ContentAccessLevel), default=ContentAccessLevel.FREE, nullable=False
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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

    subtopic: Mapped["Subtopic"] = relationship("Subtopic", back_populates="lessons")


class Concept(Base):
    """Reusable algorithmic concept taggable across topics, lessons, and problems."""

    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
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


class Tag(Base):
    """Normalized categorical tags for problem classification."""

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problems: Mapped[list["Problem"]] = relationship(
        "Problem", secondary=problem_tags, back_populates="tags"
    )


class ProblemPattern(Base):
    """Standard algorithmic solution patterns (e.g. Two Pointers, Sliding Window)."""

    __tablename__ = "patterns"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    slug: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problems: Mapped[list["Problem"]] = relationship(
        "Problem", secondary=problem_patterns, back_populates="patterns"
    )


class Problem(Base):
    """Core algorithmic problem specification."""

    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    public_id: Mapped[str] = mapped_column(
        String(36),
        default=lambda: f"prb_{uuid.uuid4().hex[:12]}",
        unique=True,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[ProblemDifficulty] = mapped_column(
        Enum(ProblemDifficulty),
        default=ProblemDifficulty.EASY,
        nullable=False,
        index=True,
    )
    access_level: Mapped[ContentAccessLevel] = mapped_column(
        Enum(ContentAccessLevel),
        default=ContentAccessLevel.FREE,
        nullable=False,
        index=True,
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.PUBLISHED, nullable=False, index=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subtopic_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("subtopics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    input_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_time_complexity: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    expected_space_complexity: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    # Execution configuration limits (Phase 5 Online Judge)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=256, nullable=False)
    output_limit_bytes: Mapped[int] = mapped_column(
        Integer, default=65536, nullable=False
    )
    comparison_mode: Mapped[str] = mapped_column(
        String(32), default="exact", nullable=False
    )
    # Stored as JSON list of language identifiers, e.g. ["python", "java", "cpp"]
    supported_languages: Mapped[str] = mapped_column(
        String(255), default='["python", "java", "cpp", "javascript"]', nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    updated_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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

    topic: Mapped[Optional["Topic"]] = relationship("Topic", back_populates="problems")
    subtopic: Mapped[Optional["Subtopic"]] = relationship(
        "Subtopic", back_populates="problems"
    )
    examples: Mapped[list["ProblemExample"]] = relationship(
        "ProblemExample",
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="ProblemExample.display_order",
    )
    hints: Mapped[list["Hint"]] = relationship(
        "Hint",
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="Hint.hint_number",
    )
    test_cases: Mapped[list["TestCase"]] = relationship(
        "TestCase",
        back_populates="problem",
        cascade="all, delete-orphan",
        order_by="TestCase.display_order",
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=problem_tags, back_populates="problems"
    )
    patterns: Mapped[list["ProblemPattern"]] = relationship(
        "ProblemPattern", secondary=problem_patterns, back_populates="problems"
    )


class ProblemExample(Base):
    """Informational examples illustrating problem statement."""

    __tablename__ = "problem_examples"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    output: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problem: Mapped["Problem"] = relationship("Problem", back_populates="examples")


class Hint(Base):
    """Progressive guidance hints for problems."""

    __tablename__ = "problem_hints"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    hint_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    title: Mapped[str] = mapped_column(String(128), default="Hint", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problem: Mapped["Problem"] = relationship("Problem", back_populates="hints")


class TestCase(Base):
    """Verification test cases for future online judging.

    SECURITY INVARIANT:
    Test cases where is_hidden == True must NEVER be exposed in student APIs.
    """

    __tablename__ = "test_cases"
    __test__ = False  # Prevent pytest from attempting to collect SQLAlchemy model as a test suite

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problem: Mapped["Problem"] = relationship("Problem", back_populates="test_cases")
