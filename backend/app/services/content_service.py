"""Content service orchestrating access rules, premium gates, publishing workflow, and sanitization."""

import json
import math
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ContentStatus,
    Curriculum,
    Lesson,
    Problem,
    ProblemDifficulty,
    Subtopic,
    Topic,
    Track,
)
from backend.app.models.user import User, UserRole
from backend.app.repositories.audit_repo import AuditRepository
from backend.app.repositories.content_repo import ContentRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.schemas.content import (
    CurriculumDetail,
    CurriculumSummary,
    HintResponse,
    LessonBlock,
    LessonDetail,
    LessonSummary,
    PaginatedData,
    PatternResponse,
    ProblemDetail,
    ProblemExampleResponse,
    ProblemSummary,
    SubtopicDetail,
    SubtopicSummary,
    TagResponse,
    TestCaseResponse,
    TopicDetail,
    TopicSummary,
    TrackSummary,
)


class ContentService:
    """Business logic for educational curriculum, lessons, problems, and access gates."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.content_repo = ContentRepository(session)
        self.user_repo = UserRepository(session)
        self.audit_repo = AuditRepository(session)

    # --- Student Reading & Gated Access ---

    async def get_curricula_list(self) -> List[CurriculumSummary]:
        """Returns all published curricula."""
        curricula = await self.content_repo.get_curricula(status=ContentStatus.PUBLISHED)
        return [CurriculumSummary.model_validate(c) for c in curricula]

    async def get_curriculum_by_slug(self, slug_or_id: str) -> CurriculumDetail:
        """Returns published curriculum with tracks."""
        curriculum = await self.content_repo.get_curriculum_by_slug_or_id(
            slug_or_id, status=ContentStatus.PUBLISHED
        )
        if not curriculum:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curriculum not found.",
            )
        return CurriculumDetail(
            id=curriculum.id,
            public_id=curriculum.public_id,
            slug=curriculum.slug,
            title=curriculum.title,
            short_description=curriculum.short_description,
            description=curriculum.description,
            level=curriculum.level,
            status=curriculum.status,
            display_order=curriculum.display_order,
            is_free=curriculum.is_free,
            tracks=[TrackSummary.model_validate(t) for t in curriculum.tracks if t.status == ContentStatus.PUBLISHED],
            created_at=curriculum.created_at,
            updated_at=curriculum.updated_at,
        )

    async def get_topics_list(
        self,
        track_id: Optional[str] = None,
        difficulty: Optional[ContentLevel] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedData[TopicSummary]:
        """Returns paginated published topics."""
        safe_page_size = min(max(page_size, 1), 100)
        safe_page = max(page, 1)

        topics, total = await self.content_repo.get_topics(
            track_id=track_id,
            difficulty=difficulty,
            page=safe_page,
            page_size=safe_page_size,
            status=ContentStatus.PUBLISHED,
        )
        total_pages = math.ceil(total / safe_page_size) if total > 0 else 1

        return PaginatedData(
            items=[TopicSummary.model_validate(t) for t in topics],
            page=safe_page,
            page_size=safe_page_size,
            total=total,
            total_pages=total_pages,
            has_next=safe_page < total_pages,
            has_prev=safe_page > 1,
        )

    async def get_topic_detail(self, slug_or_id: str) -> TopicDetail:
        """Returns published topic and its subtopics."""
        topic = await self.content_repo.get_topic_by_slug_or_id(
            slug_or_id, status=ContentStatus.PUBLISHED
        )
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Topic not found.",
            )
        return TopicDetail(
            id=topic.id,
            public_id=topic.public_id,
            track_id=topic.track_id,
            slug=topic.slug,
            title=topic.title,
            description=topic.description,
            display_order=topic.display_order,
            difficulty=topic.difficulty,
            access_level=topic.access_level,
            status=topic.status,
            subtopics=[SubtopicSummary.model_validate(st) for st in topic.subtopics if st.status == ContentStatus.PUBLISHED],
            created_at=topic.created_at,
            updated_at=topic.updated_at,
        )

    async def get_subtopic_detail(self, subtopic_id: str) -> SubtopicDetail:
        """Returns subtopic summary with counts."""
        subtopic = await self.content_repo.get_subtopic_by_id(
            subtopic_id, status=ContentStatus.PUBLISHED
        )
        if not subtopic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subtopic not found.",
            )
        return SubtopicDetail(
            id=subtopic.id,
            topic_id=subtopic.topic_id,
            slug=subtopic.slug,
            title=subtopic.title,
            description=subtopic.description,
            display_order=subtopic.display_order,
            difficulty=subtopic.difficulty,
            access_level=subtopic.access_level,
            status=subtopic.status,
            created_at=subtopic.created_at,
            updated_at=subtopic.updated_at,
        )

    async def get_lesson_detail(
        self,
        slug_or_id: str,
        current_user: Optional[User] = None,
    ) -> LessonDetail:
        """Fetches lesson with strict server-side Premium access verification."""
        lesson = await self.content_repo.get_lesson_by_slug_or_id(
            slug_or_id, status=ContentStatus.PUBLISHED
        )
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found.",
            )

        # Enforce server-side Premium gate
        if lesson.access_level == ContentAccessLevel.PREMIUM:
            is_authorized = False
            if current_user:
                if current_user.role in (UserRole.ADMIN, UserRole.CONTENT_EDITOR):
                    is_authorized = True
                else:
                    is_authorized = await self.user_repo.has_active_premium(current_user.id)

            if not is_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This lesson requires an active Premium subscription.",
                )

        # Parse structured content blocks safely
        try:
            raw_blocks = json.loads(lesson.content_json)
            blocks = [LessonBlock(**b) for b in raw_blocks]
        except Exception:
            blocks = [LessonBlock(type="paragraph", content=lesson.summary)]

        return LessonDetail(
            id=lesson.id,
            public_id=lesson.public_id,
            subtopic_id=lesson.subtopic_id,
            slug=lesson.slug,
            title=lesson.title,
            summary=lesson.summary,
            blocks=blocks,
            estimated_minutes=lesson.estimated_minutes,
            difficulty=lesson.difficulty,
            display_order=lesson.display_order,
            access_level=lesson.access_level,
            status=lesson.status,
            version=lesson.version,
            created_at=lesson.created_at,
            updated_at=lesson.updated_at,
        )

    async def get_problems_list(
        self,
        topic_slug: Optional[str] = None,
        difficulty: Optional[ProblemDifficulty] = None,
        access_level: Optional[ContentAccessLevel] = None,
        tag_slug: Optional[str] = None,
        pattern_slug: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedData[ProblemSummary]:
        """Returns paginated published problems list with filters."""
        safe_page_size = min(max(page_size, 1), 100)
        safe_page = max(page, 1)

        problems, total = await self.content_repo.get_problems(
            topic_slug=topic_slug,
            difficulty=difficulty,
            access_level=access_level,
            tag_slug=tag_slug,
            pattern_slug=pattern_slug,
            search=search,
            page=safe_page,
            page_size=safe_page_size,
            status=ContentStatus.PUBLISHED,
        )
        total_pages = math.ceil(total / safe_page_size) if total > 0 else 1

        items = [
            ProblemSummary(
                id=p.id,
                public_id=p.public_id,
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                access_level=p.access_level,
                status=p.status,
                topic_id=p.topic_id,
                subtopic_id=p.subtopic_id,
                display_order=p.display_order,
                estimated_minutes=p.estimated_minutes,
                tags=[TagResponse.model_validate(t) for t in p.tags],
                patterns=[PatternResponse.model_validate(pt) for pt in p.patterns],
            )
            for p in problems
        ]

        return PaginatedData(
            items=items,
            page=safe_page,
            page_size=safe_page_size,
            total=total,
            total_pages=total_pages,
            has_next=safe_page < total_pages,
            has_prev=safe_page > 1,
        )

    async def get_problem_detail(
        self,
        slug_or_id: str,
        current_user: Optional[User] = None,
    ) -> ProblemDetail:
        """Fetches problem specification with strict Premium verification and test case security.
        
        SECURITY INVARIANTS:
        1. Premium Gate: Free users without active entitlement receive 403 Forbidden.
        2. Hidden Test Protection: Test cases with is_hidden == True are strictly excluded.
        """
        problem = await self.content_repo.get_problem_by_slug_or_id(
            slug_or_id, status=ContentStatus.PUBLISHED
        )
        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem not found.",
            )

        # Enforce server-side Premium gate
        if problem.access_level == ContentAccessLevel.PREMIUM:
            is_authorized = False
            if current_user:
                if current_user.role in (UserRole.ADMIN, UserRole.CONTENT_EDITOR):
                    is_authorized = True
                else:
                    is_authorized = await self.user_repo.has_active_premium(current_user.id)

            if not is_authorized:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This problem requires an active Premium subscription.",
                )

        # Parse supported languages JSON safely
        try:
            langs = json.loads(problem.supported_languages)
        except Exception:
            langs = ["python", "java", "cpp", "javascript"]

        # SECURITY: Strictly sample test cases only!
        sample_test_cases = [
            TestCaseResponse.model_validate(tc)
            for tc in problem.test_cases
            if tc.is_sample and not tc.is_hidden
        ]

        return ProblemDetail(
            id=problem.id,
            public_id=problem.public_id,
            slug=problem.slug,
            title=problem.title,
            statement=problem.statement,
            explanation=problem.explanation,
            difficulty=problem.difficulty,
            access_level=problem.access_level,
            status=problem.status,
            topic_id=problem.topic_id,
            subtopic_id=problem.subtopic_id,
            display_order=problem.display_order,
            estimated_minutes=problem.estimated_minutes,
            input_format=problem.input_format,
            output_format=problem.output_format,
            constraints=problem.constraints,
            expected_time_complexity=problem.expected_time_complexity,
            expected_space_complexity=problem.expected_space_complexity,
            supported_languages=langs,
            version=problem.version,
            examples=[ProblemExampleResponse.model_validate(ex) for ex in problem.examples],
            hints=[HintResponse.model_validate(h) for h in problem.hints],
            sample_test_cases=sample_test_cases,
            tags=[TagResponse.model_validate(t) for t in problem.tags],
            patterns=[PatternResponse.model_validate(pat) for pat in problem.patterns],
            created_at=problem.created_at,
            updated_at=problem.updated_at,
        )

    # --- Content Authoring & Publishing Workflow ---

    async def update_publishing_status(
        self,
        entity_type: str,
        entity_id: str,
        new_status: ContentStatus,
        actor_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> bool:
        """Updates publishing state (DRAFT -> REVIEW -> PUBLISHED/ARCHIVED) with audit trail."""
        model_map = {
            "curriculum": Curriculum,
            "topic": Topic,
            "subtopic": Subtopic,
            "lesson": Lesson,
            "problem": Problem,
        }
        model = model_map.get(entity_type.lower())
        if not model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type: {entity_type}",
            )

        updated = await self.content_repo.update_status(
            model=model,
            entity_id=entity_id,
            status=new_status,
            updated_by=actor_id,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.capitalize()} not found.",
            )

        await self.audit_repo.log_event(
            action=f"content.{entity_type}.status_updated",
            actor_id=actor_id,
            target_type=entity_type,
            target_id=entity_id,
            ip_address=ip_address,
            request_id=request_id,
            metadata_json=json.dumps({"new_status": new_status.value}),
        )
        return True
