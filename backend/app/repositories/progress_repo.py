"""Repository layer for progress, submissions, mistakes notebook, and spaced revision."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import (
    and_,
    desc,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.content import (
    ContentStatus,
    Lesson,
    Problem,
    Subtopic,
    Topic,
)
from backend.app.models.progress import (
    LessonProgressStatus,
    Mistake,
    MistakeType,
    ProblemProgressStatus,
    ReviewOutcome,
    RevisionItem,
    RevisionSchedule,
    RevisionScheduleStatus,
    RevisionSourceType,
    Submission,
    SubmissionStatus,
    UserLessonProgress,
    UserProblemProgress,
)


class ProgressRepository:
    """Handles data access and atomic queries for learning progress and submissions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Lesson Progress
    # -----------------------------------------------------------------------

    async def get_user_lesson_progress(
        self, user_id: str, lesson_id: str
    ) -> UserLessonProgress | None:
        stmt = select(UserLessonProgress).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.lesson_id == lesson_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def record_lesson_start(
        self, user_id: str, lesson_id: str
    ) -> UserLessonProgress:
        prog = await self.get_user_lesson_progress(user_id, lesson_id)
        now = datetime.now(timezone.utc)
        if not prog:
            prog = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status=LessonProgressStatus.IN_PROGRESS,
                started_at=now,
                last_viewed_at=now,
                progress_percent=25,
            )
            self.db.add(prog)
        else:
            prog.last_viewed_at = now
            if prog.status == LessonProgressStatus.NOT_STARTED:
                prog.status = LessonProgressStatus.IN_PROGRESS
                prog.started_at = now
                prog.progress_percent = max(prog.progress_percent, 25)
        await self.db.flush()
        return prog

    async def record_lesson_complete(
        self, user_id: str, lesson_id: str
    ) -> UserLessonProgress:
        prog = await self.get_user_lesson_progress(user_id, lesson_id)
        now = datetime.now(timezone.utc)
        if not prog:
            prog = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status=LessonProgressStatus.COMPLETED,
                started_at=now,
                completed_at=now,
                last_viewed_at=now,
                progress_percent=100,
            )
            self.db.add(prog)
        else:
            prog.status = LessonProgressStatus.COMPLETED
            if not prog.started_at:
                prog.started_at = now
            prog.completed_at = now
            prog.last_viewed_at = now
            prog.progress_percent = 100
        await self.db.flush()
        return prog

    # -----------------------------------------------------------------------
    # Problem Progress
    # -----------------------------------------------------------------------

    async def get_user_problem_progress(
        self, user_id: str, problem_id: str
    ) -> UserProblemProgress | None:
        stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.problem_id == problem_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def record_problem_attempt(
        self, user_id: str, problem_id: str
    ) -> UserProblemProgress:
        prog = await self.get_user_problem_progress(user_id, problem_id)
        now = datetime.now(timezone.utc)
        if not prog:
            prog = UserProblemProgress(
                user_id=user_id,
                problem_id=problem_id,
                status=ProblemProgressStatus.ATTEMPTED,
                attempts_count=1,
                first_attempted_at=now,
                last_attempted_at=now,
            )
            self.db.add(prog)
        else:
            prog.attempts_count += 1
            prog.last_attempted_at = now
            if not prog.first_attempted_at:
                prog.first_attempted_at = now
            if prog.status == ProblemProgressStatus.NOT_STARTED:
                prog.status = ProblemProgressStatus.ATTEMPTED
        await self.db.flush()
        return prog

    async def record_problem_solved(
        self, user_id: str, problem_id: str
    ) -> UserProblemProgress:
        prog = await self.get_user_problem_progress(user_id, problem_id)
        now = datetime.now(timezone.utc)
        if not prog:
            prog = UserProblemProgress(
                user_id=user_id,
                problem_id=problem_id,
                status=ProblemProgressStatus.SOLVED,
                attempts_count=1,
                successful_attempts=1,
                first_attempted_at=now,
                last_attempted_at=now,
                solved_at=now,
            )
            self.db.add(prog)
        else:
            prog.status = ProblemProgressStatus.SOLVED
            prog.successful_attempts += 1
            if not prog.solved_at:
                prog.solved_at = now
            prog.last_attempted_at = now
        await self.db.flush()
        return prog

    # -----------------------------------------------------------------------
    # Aggregate Metrics & Overview
    # -----------------------------------------------------------------------

    async def get_total_visible_lessons(self) -> int:
        stmt = select(func.count(Lesson.id)).where(
            Lesson.status == ContentStatus.PUBLISHED
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def get_total_visible_problems(self) -> int:
        stmt = select(func.count(Problem.id)).where(
            Problem.status == ContentStatus.PUBLISHED
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def count_user_completed_lessons(self, user_id: str) -> int:
        stmt = select(func.count(UserLessonProgress.id)).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status == LessonProgressStatus.COMPLETED,
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def count_user_started_lessons(self, user_id: str) -> int:
        stmt = select(func.count(UserLessonProgress.id)).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.status.in_(
                [LessonProgressStatus.IN_PROGRESS, LessonProgressStatus.COMPLETED]
            ),
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def count_user_solved_problems(self, user_id: str) -> int:
        stmt = select(func.count(UserProblemProgress.id)).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.status == ProblemProgressStatus.SOLVED,
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def count_user_attempted_problems(self, user_id: str) -> int:
        stmt = select(func.count(UserProblemProgress.id)).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.status.in_(
                [ProblemProgressStatus.ATTEMPTED, ProblemProgressStatus.SOLVED]
            ),
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def get_recent_activity(
        self, user_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieves recent learning events across lessons and problems."""
        # 1. Recent lesson progress
        lesson_stmt = (
            select(
                Lesson.title,
                Lesson.slug,
                UserLessonProgress.status,
                UserLessonProgress.updated_at,
            )
            .join(Lesson, UserLessonProgress.lesson_id == Lesson.id)
            .where(UserLessonProgress.user_id == user_id)
            .order_by(desc(UserLessonProgress.updated_at))
            .limit(limit)
        )
        lesson_res = (await self.db.execute(lesson_stmt)).all()

        # 2. Recent problem progress
        problem_stmt = (
            select(
                Problem.title,
                Problem.slug,
                UserProblemProgress.status,
                UserProblemProgress.updated_at,
            )
            .join(Problem, UserProblemProgress.problem_id == Problem.id)
            .where(UserProblemProgress.user_id == user_id)
            .order_by(desc(UserProblemProgress.updated_at))
            .limit(limit)
        )
        problem_res = (await self.db.execute(problem_stmt)).all()

        combined = []
        for r in lesson_res:
            combined.append(
                {
                    "title": r[0],
                    "slug": r[1],
                    "entity_type": "LESSON",
                    "status": r[2].value if hasattr(r[2], "value") else str(r[2]),
                    "timestamp": r[3],
                }
            )
        for r in problem_res:
            combined.append(
                {
                    "title": r[0],
                    "slug": r[1],
                    "entity_type": "PROBLEM",
                    "status": r[2].value if hasattr(r[2], "value") else str(r[2]),
                    "timestamp": r[3],
                }
            )

        combined.sort(key=lambda x: x["timestamp"], reverse=True)
        return combined[:limit]

    async def get_topic_progress(
        self, user_id: str, topic_id_or_slug: str
    ) -> dict[str, Any] | None:
        """Calculates child aggregate metrics for a given topic."""
        # Find topic
        topic_stmt = select(Topic).where(
            or_(Topic.id == topic_id_or_slug, Topic.slug == topic_id_or_slug),
            Topic.status == ContentStatus.PUBLISHED,
        )
        topic = (await self.db.execute(topic_stmt)).scalar_one_or_none()
        if not topic:
            return None

        # Published lessons under this topic
        lessons_stmt = (
            select(Lesson.id)
            .join(Subtopic, Lesson.subtopic_id == Subtopic.id)
            .where(
                Subtopic.topic_id == topic.id, Lesson.status == ContentStatus.PUBLISHED
            )
        )
        lesson_ids = (await self.db.execute(lessons_stmt)).scalars().all()

        # Published problems under this topic
        problems_stmt = (
            select(Problem.id)
            .join(Subtopic, Problem.subtopic_id == Subtopic.id)
            .where(
                Subtopic.topic_id == topic.id, Problem.status == ContentStatus.PUBLISHED
            )
        )
        problem_ids = (await self.db.execute(problems_stmt)).scalars().all()

        completed_lessons = 0
        if lesson_ids:
            c_stmt = select(func.count(UserLessonProgress.id)).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_id.in_(lesson_ids),
                UserLessonProgress.status == LessonProgressStatus.COMPLETED,
            )
            completed_lessons = (await self.db.execute(c_stmt)).scalar() or 0

        solved_problems = 0
        if problem_ids:
            s_stmt = select(func.count(UserProblemProgress.id)).where(
                UserProblemProgress.user_id == user_id,
                UserProblemProgress.problem_id.in_(problem_ids),
                UserProblemProgress.status == ProblemProgressStatus.SOLVED,
            )
            solved_problems = (await self.db.execute(s_stmt)).scalar() or 0

        total_items = len(lesson_ids) + len(problem_ids)
        completed_items = completed_lessons + solved_problems
        percent = (
            round((completed_items / total_items) * 100, 1) if total_items > 0 else 0.0
        )

        return {
            "topic_id": topic.id,
            "topic_title": topic.title,
            "topic_slug": topic.slug,
            "total_lessons": len(lesson_ids),
            "completed_lessons": completed_lessons,
            "total_problems": len(problem_ids),
            "solved_problems": solved_problems,
            "completion_percent": percent,
        }

    # -----------------------------------------------------------------------
    # Submissions
    # -----------------------------------------------------------------------

    async def get_submission_by_idempotency_key(
        self, user_id: str, idempotency_key: str
    ) -> Submission | None:
        stmt = (
            select(Submission)
            .options(selectinload(Submission.problem))
            .where(
                Submission.user_id == user_id,
                Submission.idempotency_key == idempotency_key,
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def create_submission(
        self,
        user_id: str,
        problem_id: str,
        language: str,
        source_code: str,
        idempotency_key: str | None = None,
        metadata_json: dict[str, Any] | None = None,
    ) -> Submission:
        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            language=language,
            source_code=source_code,
            status=SubmissionStatus.QUEUED_FOR_FUTURE_JUDGE,
            idempotency_key=idempotency_key,
            metadata_json=metadata_json,
        )
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def list_user_submissions(
        self,
        user_id: str,
        problem_id: str | None = None,
        language: str | None = None,
        status: SubmissionStatus | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Submission], int]:
        filters = [Submission.user_id == user_id]
        if problem_id:
            filters.append(Submission.problem_id == problem_id)
        if language:
            filters.append(Submission.language == language.strip().lower())
        if status:
            filters.append(Submission.status == status)

        count_stmt = select(func.count(Submission.id)).where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        query = (
            select(Submission)
            .options(
                selectinload(Submission.problem),
                selectinload(Submission.result),
            )
            .where(and_(*filters))
            .order_by(desc(Submission.created_at))
            .limit(limit)
            .offset(offset)
        )
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def get_user_submission_by_id(
        self, submission_id: str, user_id: str
    ) -> Submission | None:
        """Ownership-safe retrieval: strictly matches user_id."""
        stmt = (
            select(Submission)
            .options(
                selectinload(Submission.problem),
                selectinload(Submission.result),
            )
            .where(
                or_(
                    Submission.id == submission_id,
                    Submission.public_id == submission_id,
                ),
                Submission.user_id == user_id,
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Mistake Notebook
    # -----------------------------------------------------------------------

    async def create_mistake(
        self,
        user_id: str,
        title: str,
        description: str,
        mistake_type: MistakeType,
        correction: str | None = None,
        problem_id: str | None = None,
        lesson_id: str | None = None,
    ) -> Mistake:
        mistake = Mistake(
            user_id=user_id,
            title=title,
            description=description,
            mistake_type=mistake_type,
            correction=correction,
            problem_id=problem_id,
            lesson_id=lesson_id,
        )
        self.db.add(mistake)
        await self.db.flush()
        return mistake

    async def get_user_mistake_by_id(
        self, mistake_id: str, user_id: str
    ) -> Mistake | None:
        stmt = (
            select(Mistake)
            .options(selectinload(Mistake.problem), selectinload(Mistake.lesson))
            .where(
                or_(Mistake.id == mistake_id, Mistake.public_id == mistake_id),
                Mistake.user_id == user_id,
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_user_mistakes(
        self,
        user_id: str,
        is_resolved: bool | None = None,
        mistake_type: MistakeType | None = None,
        problem_id: str | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Mistake], int]:
        filters = [Mistake.user_id == user_id]
        if is_resolved is not None:
            filters.append(Mistake.is_resolved == is_resolved)
        if mistake_type is not None:
            filters.append(Mistake.mistake_type == mistake_type)
        if problem_id:
            filters.append(Mistake.problem_id == problem_id)
        if search and search.strip():
            term = f"%{search.strip()[:100]}%"
            filters.append(
                or_(Mistake.title.ilike(term), Mistake.description.ilike(term))
            )

        count_stmt = select(func.count(Mistake.id)).where(and_(*filters))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        query = (
            select(Mistake)
            .options(selectinload(Mistake.problem), selectinload(Mistake.lesson))
            .where(and_(*filters))
            .order_by(desc(Mistake.created_at))
            .limit(limit)
            .offset(offset)
        )
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def count_unresolved_mistakes(self, user_id: str) -> int:
        stmt = select(func.count(Mistake.id)).where(
            Mistake.user_id == user_id,
            Mistake.is_resolved.is_(False),
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def delete_user_mistake(self, mistake: Mistake) -> None:
        await self.db.delete(mistake)
        await self.db.flush()

    # -----------------------------------------------------------------------
    # Spaced Revision
    # -----------------------------------------------------------------------

    async def create_revision_item(
        self,
        user_id: str,
        source_type: RevisionSourceType,
        source_id: str,
        title: str,
        priority: int = 1,
    ) -> RevisionItem:
        # Check existing item to prevent duplication
        stmt = (
            select(RevisionItem)
            .options(selectinload(RevisionItem.schedule))
            .where(
                RevisionItem.user_id == user_id,
                RevisionItem.source_type == source_type,
                RevisionItem.source_id == source_id,
            )
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.title = title
            existing.priority = priority
            existing.is_active = True
            await self.db.flush()
            return existing

        item = RevisionItem(
            user_id=user_id,
            source_type=source_type,
            source_id=source_id,
            title=title,
            priority=priority,
            is_active=True,
        )
        self.db.add(item)
        await self.db.flush()

        # Create schedule with initial 1 day interval
        now = datetime.now(timezone.utc)
        schedule = RevisionSchedule(
            revision_item_id=item.id,
            due_at=now + timedelta(days=1),
            interval_days=1.0,
            ease_factor=2.5,
            status=RevisionScheduleStatus.ACTIVE,
        )
        self.db.add(schedule)
        await self.db.flush()

        # Reload with schedule
        return await self.get_user_revision_item_by_id(item.id, user_id)  # type: ignore

    async def get_user_revision_item_by_id(
        self, item_id: str, user_id: str
    ) -> RevisionItem | None:
        stmt = (
            select(RevisionItem)
            .options(selectinload(RevisionItem.schedule))
            .where(
                or_(RevisionItem.id == item_id, RevisionItem.public_id == item_id),
                RevisionItem.user_id == user_id,
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_due_revision_items(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> tuple[list[RevisionItem], int]:
        """Lists active revision items that are due now or upcoming."""
        count_stmt = (
            select(func.count(RevisionItem.id))
            .join(
                RevisionSchedule, RevisionItem.id == RevisionSchedule.revision_item_id
            )
            .where(
                RevisionItem.user_id == user_id,
                RevisionItem.is_active.is_(True),
                RevisionSchedule.status == RevisionScheduleStatus.ACTIVE,
            )
        )
        total = (await self.db.execute(count_stmt)).scalar() or 0

        query = (
            select(RevisionItem)
            .options(selectinload(RevisionItem.schedule))
            .join(
                RevisionSchedule, RevisionItem.id == RevisionSchedule.revision_item_id
            )
            .where(
                RevisionItem.user_id == user_id,
                RevisionItem.is_active.is_(True),
                RevisionSchedule.status == RevisionScheduleStatus.ACTIVE,
            )
            .order_by(RevisionSchedule.due_at.asc(), desc(RevisionItem.priority))
            .limit(limit)
            .offset(offset)
        )
        items = (await self.db.execute(query)).scalars().all()
        return list(items), total

    async def count_due_items(self, user_id: str) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            select(func.count(RevisionItem.id))
            .join(
                RevisionSchedule, RevisionItem.id == RevisionSchedule.revision_item_id
            )
            .where(
                RevisionItem.user_id == user_id,
                RevisionItem.is_active.is_(True),
                RevisionSchedule.status == RevisionScheduleStatus.ACTIVE,
                RevisionSchedule.due_at <= now,
            )
        )
        return (await self.db.execute(stmt)).scalar() or 0

    async def apply_review_outcome(
        self, item: RevisionItem, outcome: ReviewOutcome
    ) -> RevisionSchedule:
        """Deterministic spaced repetition scheduling algorithm."""
        sched = item.schedule
        if not sched:
            now = datetime.now(timezone.utc)
            sched = RevisionSchedule(
                revision_item_id=item.id,
                due_at=now + timedelta(days=1),
                interval_days=1.0,
                ease_factor=2.5,
                status=RevisionScheduleStatus.ACTIVE,
            )
            self.db.add(sched)

        now = datetime.now(timezone.utc)
        sched.last_reviewed_at = now

        # Algorithm parameters:
        # AGAIN: Reset streak, interval = 0.5 days, lower ease
        # HARD: Slight interval increase, slight ease drop
        # GOOD: Standard multiplier = ease_factor
        # EASY: Higher multiplier = ease_factor * 1.3, ease increase
        if outcome == ReviewOutcome.AGAIN:
            sched.interval_days = 0.5
            sched.ease_factor = max(1.3, sched.ease_factor - 0.2)
            sched.review_count = 0
        elif outcome == ReviewOutcome.HARD:
            sched.interval_days = max(1.0, round(sched.interval_days * 1.2, 1))
            sched.ease_factor = max(1.3, sched.ease_factor - 0.15)
            sched.review_count += 1
        elif outcome == ReviewOutcome.GOOD:
            sched.interval_days = max(
                1.0, round(sched.interval_days * sched.ease_factor, 1)
            )
            sched.review_count += 1
        elif outcome == ReviewOutcome.EASY:
            sched.interval_days = max(
                2.0, round(sched.interval_days * sched.ease_factor * 1.3, 1)
            )
            sched.ease_factor = min(3.0, sched.ease_factor + 0.15)
            sched.review_count += 1

        sched.due_at = now + timedelta(days=sched.interval_days)
        sched.status = RevisionScheduleStatus.ACTIVE
        await self.db.flush()
        return sched
