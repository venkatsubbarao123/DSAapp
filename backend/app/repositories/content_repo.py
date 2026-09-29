"""Content repository managing parameterized database operations for curricula, topics, lessons, and problems."""

import json
import math
from typing import Any, Dict, List, Optional, Tuple, Type
from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.content import (
    Concept,
    ContentAccessLevel,
    ContentLevel,
    ContentStatus,
    Curriculum,
    Hint,
    Lesson,
    Problem,
    ProblemDifficulty,
    ProblemExample,
    ProblemPattern,
    Subtopic,
    Tag,
    TestCase,
    Topic,
    Track,
    problem_patterns,
    problem_tags,
)


class ContentRepository:
    """Encapsulates transactional queries and filtering for educational content."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Curricula & Tracks ---

    async def get_curricula(
        self, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> List[Curriculum]:
        """Fetches active curricula ordered by display_order."""
        stmt = select(Curriculum).order_by(Curriculum.display_order.asc())
        if status is not None:
            stmt = stmt.where(Curriculum.status == status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_curriculum_by_slug_or_id(
        self, slug_or_id: str, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> Optional[Curriculum]:
        """Fetches curriculum with nested tracks eager-loaded."""
        stmt = (
            select(Curriculum)
            .where(or_(Curriculum.slug == slug_or_id, Curriculum.id == slug_or_id, Curriculum.public_id == slug_or_id))
            .options(selectinload(Curriculum.tracks))
        )
        if status is not None:
            stmt = stmt.where(Curriculum.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_track_by_slug_or_id(
        self, slug_or_id: str, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> Optional[Track]:
        """Fetches track with nested topics eager-loaded."""
        stmt = (
            select(Track)
            .where(or_(Track.slug == slug_or_id, Track.id == slug_or_id))
            .options(selectinload(Track.topics))
        )
        if status is not None:
            stmt = stmt.where(Track.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Topics & Subtopics ---

    async def get_topics(
        self,
        track_id: Optional[str] = None,
        difficulty: Optional[ContentLevel] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ContentStatus] = ContentStatus.PUBLISHED,
    ) -> Tuple[List[Topic], int]:
        """Returns paginated list of topics with filters."""
        stmt = select(Topic).order_by(Topic.display_order.asc(), Topic.created_at.desc())
        count_stmt = select(func.count(Topic.id))

        if status is not None:
            stmt = stmt.where(Topic.status == status)
            count_stmt = count_stmt.where(Topic.status == status)

        if track_id:
            stmt = stmt.where(Topic.track_id == track_id)
            count_stmt = count_stmt.where(Topic.track_id == track_id)

        if difficulty:
            stmt = stmt.where(Topic.difficulty == difficulty)
            count_stmt = count_stmt.where(Topic.difficulty == difficulty)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_topic_by_slug_or_id(
        self, slug_or_id: str, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> Optional[Topic]:
        """Fetches topic with subtopics eager-loaded."""
        stmt = (
            select(Topic)
            .where(or_(Topic.slug == slug_or_id, Topic.id == slug_or_id, Topic.public_id == slug_or_id))
            .options(selectinload(Topic.subtopics))
        )
        if status is not None:
            stmt = stmt.where(Topic.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_subtopic_by_id(
        self, subtopic_id: str, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> Optional[Subtopic]:
        """Fetches subtopic by ID."""
        stmt = select(Subtopic).where(Subtopic.id == subtopic_id)
        if status is not None:
            stmt = stmt.where(Subtopic.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Lessons ---

    async def get_lessons(
        self,
        subtopic_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ContentStatus] = ContentStatus.PUBLISHED,
    ) -> Tuple[List[Lesson], int]:
        """Returns paginated lessons list."""
        stmt = select(Lesson).order_by(Lesson.display_order.asc(), Lesson.created_at.desc())
        count_stmt = select(func.count(Lesson.id))

        if status is not None:
            stmt = stmt.where(Lesson.status == status)
            count_stmt = count_stmt.where(Lesson.status == status)

        if subtopic_id:
            stmt = stmt.where(Lesson.subtopic_id == subtopic_id)
            count_stmt = count_stmt.where(Lesson.subtopic_id == subtopic_id)

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_lesson_by_slug_or_id(
        self, slug_or_id: str, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> Optional[Lesson]:
        """Fetches single lesson by unique identifier."""
        stmt = select(Lesson).where(
            or_(Lesson.slug == slug_or_id, Lesson.id == slug_or_id, Lesson.public_id == slug_or_id)
        )
        if status is not None:
            stmt = stmt.where(Lesson.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Problems ---

    async def get_problems(
        self,
        topic_slug: Optional[str] = None,
        difficulty: Optional[ProblemDifficulty] = None,
        access_level: Optional[ContentAccessLevel] = None,
        tag_slug: Optional[str] = None,
        pattern_slug: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ContentStatus] = ContentStatus.PUBLISHED,
    ) -> Tuple[List[Problem], int]:
        """Fetches filtered and paginated problem summaries."""
        stmt = (
            select(Problem)
            .options(
                selectinload(Problem.tags),
                selectinload(Problem.patterns),
            )
            .order_by(Problem.display_order.asc(), Problem.created_at.desc())
        )
        count_stmt = select(func.count(func.distinct(Problem.id)))

        if status is not None:
            stmt = stmt.where(Problem.status == status)
            count_stmt = count_stmt.where(Problem.status == status)

        if difficulty:
            stmt = stmt.where(Problem.difficulty == difficulty)
            count_stmt = count_stmt.where(Problem.difficulty == difficulty)

        if access_level:
            stmt = stmt.where(Problem.access_level == access_level)
            count_stmt = count_stmt.where(Problem.access_level == access_level)

        if topic_slug:
            stmt = stmt.join(Problem.topic).where(Topic.slug == topic_slug)
            count_stmt = count_stmt.join(Problem.topic).where(Topic.slug == topic_slug)

        if tag_slug:
            stmt = stmt.join(Problem.tags).where(Tag.slug == tag_slug)
            count_stmt = count_stmt.join(Problem.tags).where(Tag.slug == tag_slug)

        if pattern_slug:
            stmt = stmt.join(Problem.patterns).where(ProblemPattern.slug == pattern_slug)
            count_stmt = count_stmt.join(Problem.patterns).where(ProblemPattern.slug == pattern_slug)

        if search:
            # Safe parameterized search limited to title and slug
            search_pattern = f"%{search.strip()}%"
            stmt = stmt.where(or_(Problem.title.ilike(search_pattern), Problem.slug.ilike(search_pattern)))
            count_stmt = count_stmt.where(or_(Problem.title.ilike(search_pattern), Problem.slug.ilike(search_pattern)))

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_problem_by_slug_or_id(
        self, slug_or_id: str, status: Optional[ContentStatus] = ContentStatus.PUBLISHED
    ) -> Optional[Problem]:
        """Fetches problem with full relations eager-loaded.
        
        SECURITY INVARIANT:
        Loads examples, hints, tags, patterns, and test_cases.
        """
        stmt = (
            select(Problem)
            .where(or_(Problem.slug == slug_or_id, Problem.id == slug_or_id, Problem.public_id == slug_or_id))
            .options(
                selectinload(Problem.examples),
                selectinload(Problem.hints),
                selectinload(Problem.test_cases),
                selectinload(Problem.tags),
                selectinload(Problem.patterns),
            )
        )
        if status is not None:
            stmt = stmt.where(Problem.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # --- Tags and Patterns Helpers ---

    async def get_or_create_tag(self, name: str) -> Tag:
        """Retrieves existing tag or registers new normalized tag."""
        slug = name.strip().lower().replace(" ", "-")
        stmt = select(Tag).where(Tag.slug == slug)
        res = await self.session.execute(stmt)
        tag = res.scalar_one_or_none()
        if not tag:
            tag = Tag(slug=slug, name=name.strip())
            self.session.add(tag)
            await self.session.flush()
        return tag

    async def get_or_create_pattern(self, name: str, description: str = "") -> ProblemPattern:
        """Retrieves existing pattern or registers new pattern."""
        slug = name.strip().lower().replace(" ", "-")
        stmt = select(ProblemPattern).where(ProblemPattern.slug == slug)
        res = await self.session.execute(stmt)
        pattern = res.scalar_one_or_none()
        if not pattern:
            pattern = ProblemPattern(slug=slug, name=name.strip(), description=description)
            self.session.add(pattern)
            await self.session.flush()
        return pattern

    # --- Authoring & Administration Writes ---

    async def create_curriculum(self, data: Dict[str, Any]) -> Curriculum:
        curriculum = Curriculum(**data)
        self.session.add(curriculum)
        await self.session.flush()
        return curriculum

    async def create_track(self, data: Dict[str, Any]) -> Track:
        track = Track(**data)
        self.session.add(track)
        await self.session.flush()
        return track

    async def create_topic(self, data: Dict[str, Any]) -> Topic:
        topic = Topic(**data)
        self.session.add(topic)
        await self.session.flush()
        return topic

    async def create_subtopic(self, data: Dict[str, Any]) -> Subtopic:
        subtopic = Subtopic(**data)
        self.session.add(subtopic)
        await self.session.flush()
        return subtopic

    async def create_lesson(self, data: Dict[str, Any]) -> Lesson:
        lesson = Lesson(**data)
        self.session.add(lesson)
        await self.session.flush()
        return lesson

    async def create_problem(
        self,
        problem_data: Dict[str, Any],
        tag_names: List[str] = [],
        pattern_names: List[str] = [],
    ) -> Problem:
        problem = Problem(**problem_data)
        for tname in tag_names:
            tag = await self.get_or_create_tag(tname)
            problem.tags.append(tag)
        for pname in pattern_names:
            pat = await self.get_or_create_pattern(pname)
            problem.patterns.append(pat)
        self.session.add(problem)
        await self.session.flush()
        return problem

    async def update_status(
        self,
        model: Type[Any],
        entity_id: str,
        status: ContentStatus,
        updated_by: Optional[str] = None,
    ) -> bool:
        """Updates publishing status for content models."""
        values: Dict[str, Any] = {"status": status}
        if updated_by and hasattr(model, "updated_by"):
            values["updated_by"] = updated_by
        stmt = update(model).where(model.id == entity_id).values(**values)
        res = await self.session.execute(stmt)
        return res.rowcount > 0
