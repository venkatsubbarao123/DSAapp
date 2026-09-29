"""Database tests for Phase 3 content models, unique constraints, and relationships."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.models.content import (
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
)


@pytest.mark.asyncio
async def test_seed_development_content_is_idempotent():
    """Seed data populates curriculum hierarchy and runs idempotently without duplicates."""
    async with async_session_factory() as session:
        # First seed
        await seed_development_content(session)
        # Second seed should be a no-op
        await seed_development_content(session)

        # Verify curriculum
        curr_res = await session.execute(select(Curriculum).where(Curriculum.slug == "core-dsa-seed"))
        curriculum = curr_res.scalar_one_or_none()
        assert curriculum is not None
        assert curriculum.title == "Core Data Structures & Algorithms (Dev Seed)"

        # Verify problems
        probs_res = await session.execute(select(Problem))
        problems = probs_res.scalars().all()
        assert len(problems) >= 3


@pytest.mark.asyncio
async def test_curriculum_and_hierarchy_relationships():
    """Curriculum -> Track -> Topic -> Subtopic -> Lesson cascade and relations."""
    async with async_session_factory() as session:
        curr = Curriculum(
            slug="test-curr-hierarchy",
            title="Hierarchy Curriculum",
            description="Testing hierarchy relationships",
            level=ContentLevel.BEGINNER,
        )
        session.add(curr)
        await session.flush()

        track = Track(
            curriculum_id=curr.id,
            slug="test-track-1",
            title="Track One",
            description="Testing track",
        )
        session.add(track)
        await session.flush()

        topic = Topic(
            track_id=track.id,
            slug="test-topic-1",
            title="Topic One",
            description="Testing topic",
        )
        session.add(topic)
        await session.flush()

        subtopic = Subtopic(
            topic_id=topic.id,
            slug="test-subtopic-1",
            title="Subtopic One",
            description="Testing subtopic",
        )
        session.add(subtopic)
        await session.flush()

        lesson = Lesson(
            subtopic_id=subtopic.id,
            slug="test-lesson-1",
            title="Lesson One",
            summary="Lesson Summary",
            content_json='[{"type":"paragraph","content":"Test block"}]',
        )
        session.add(lesson)
        await session.commit()

        # Query back and verify relations with eager loading
        stmt = (
            select(Curriculum)
            .where(Curriculum.id == curr.id)
            .options(
                selectinload(Curriculum.tracks)
                .selectinload(Track.topics)
                .selectinload(Topic.subtopics)
                .selectinload(Subtopic.lessons)
            )
        )
        res = await session.execute(stmt)
        q_curr = res.scalar_one()
        assert len(q_curr.tracks) == 1
        assert len(q_curr.tracks[0].topics) == 1
        assert len(q_curr.tracks[0].topics[0].subtopics) == 1
        assert len(q_curr.tracks[0].topics[0].subtopics[0].lessons) == 1


@pytest.mark.asyncio
async def test_unique_slug_constraints_enforced():
    """Duplicate slugs for curricula, topics, and problems must raise IntegrityError."""
    async with async_session_factory() as session:
        c1 = Curriculum(slug="duplicate-slug", title="Curriculum 1", description="desc")
        session.add(c1)
        await session.commit()

        # Attempt duplicate slug
        c2 = Curriculum(slug="duplicate-slug", title="Curriculum 2", description="desc")
        session.add(c2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_problem_tags_and_patterns_associations():
    """Problems link correctly with many-to-many Tags and ProblemPatterns."""
    async with async_session_factory() as session:
        tag1 = Tag(slug="unit-test-tag", name="Unit Test Tag")
        pattern1 = ProblemPattern(slug="unit-test-pattern", name="Unit Test Pattern", description="desc")
        session.add_all([tag1, pattern1])
        await session.flush()

        problem = Problem(
            slug="tagged-problem",
            title="Tagged Problem",
            statement="Statement here",
            difficulty=ProblemDifficulty.EASY,
            access_level=ContentAccessLevel.FREE,
        )
        problem.tags.append(tag1)
        problem.patterns.append(pattern1)
        session.add(problem)
        await session.commit()

        # Verify associations
        q_prob = await session.get(Problem, problem.id)
        assert len(q_prob.tags) == 1
        assert q_prob.tags[0].slug == "unit-test-tag"
        assert len(q_prob.patterns) == 1
        assert q_prob.patterns[0].slug == "unit-test-pattern"
