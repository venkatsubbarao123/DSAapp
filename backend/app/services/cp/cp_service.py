"""Competitive Programming Domain Service.

Manages:
- CP Problem catalog by rating band (800 to 2400+)
- Input/output specifications and competitive constraints
- Server-authoritative Competitive Rating distinct from practice rating
- Competitive ranking leaderboard
"""

import logging
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.content import ContentStatus, Problem, Tag
from backend.app.models.cp import (
    CPProblemMetadata,
    CompetitiveRating,
    CompetitiveRatingHistory,
)
from backend.app.models.progress import Submission, SubmissionStatus
from backend.app.models.user import User
from backend.app.schemas.cp import (
    CPLeaderboardEntry,
    CPLeaderboardResponse,
    CPProblemDetail,
    CPProblemSummary,
    CPRatingProfile,
    CPSampleTestCase,
)

logger = logging.getLogger(__name__)


def get_rank_title(rating: int) -> str:
    """Returns competitive programming title based on Elo rating."""
    if rating >= 2200:
        return "Grandmaster"
    elif rating >= 1900:
        return "Master"
    elif rating >= 1600:
        return "Expert"
    elif rating >= 1400:
        return "Specialist"
    elif rating >= 1200:
        return "Pupil"
    else:
        return "Novice"


class CPService:
    """Competitive Programming engine service."""

    @classmethod
    async def get_or_create_rating(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> CompetitiveRating:
        """Retrieves or creates initial competitive rating record (1200 baseline)."""
        stmt = select(CompetitiveRating).where(CompetitiveRating.user_id == user_id)
        rating_obj = (await db.execute(stmt)).scalars().first()
        if not rating_obj:
            rating_obj = CompetitiveRating(
                user_id=user_id,
                current_rating=1200,
                peak_rating=1200,
            )
            db.add(rating_obj)
            await db.flush()
        return rating_obj

    @classmethod
    async def adjust_rating(
        cls,
        db: AsyncSession,
        user_id: str,
        delta: int,
        reason: str,
        source_id: Optional[str] = None,
    ) -> int:
        """Server-authoritatively updates competitive rating and logs history audit."""
        rating_obj = await cls.get_or_create_rating(db, user_id)
        prev = rating_obj.current_rating
        new_val = max(100, prev + delta)

        rating_obj.current_rating = new_val
        if new_val > rating_obj.peak_rating:
            rating_obj.peak_rating = new_val

        history = CompetitiveRatingHistory(
            user_id=user_id,
            previous_rating=prev,
            new_rating=new_val,
            delta=delta,
            reason=reason,
            source_id=source_id,
        )
        db.add(history)
        await db.commit()
        return new_val

    @classmethod
    async def list_cp_problems(
        cls,
        db: AsyncSession,
        user_id: Optional[str] = None,
        rating_band: Optional[int] = None,
        difficulty: Optional[str] = None,
    ) -> List[CPProblemSummary]:
        """Lists competitive programming problems filtered by rating band and difficulty."""
        stmt = (
            select(Problem, CPProblemMetadata)
            .join(CPProblemMetadata, Problem.id == CPProblemMetadata.problem_id)
            .where(Problem.status == ContentStatus.PUBLISHED)
            .options(selectinload(Problem.tags))
        )
        if rating_band:
            stmt = stmt.where(CPProblemMetadata.rating_band == rating_band)
        if difficulty:
            stmt = stmt.where(Problem.difficulty == difficulty)

        stmt = stmt.order_by(CPProblemMetadata.rating_band.asc(), Problem.title.asc())
        res = await db.execute(stmt)
        rows = res.all()

        # Check solved status
        solved_problem_ids = set()
        if user_id:
            sub_stmt = select(Submission.problem_id).where(
                Submission.user_id == user_id,
                Submission.status == SubmissionStatus.ACCEPTED,
            ).distinct()
            s_res = await db.execute(sub_stmt)
            solved_problem_ids = {r[0] for r in s_res.all()}

        summaries = []
        for problem, cp_meta in rows:
            tag_names = [t.name for t in problem.tags] if problem.tags else []
            summaries.append(
                CPProblemSummary(
                    id=cp_meta.id,
                    problem_id=problem.id,
                    title=problem.title,
                    slug=problem.slug,
                    rating_band=cp_meta.rating_band,
                    difficulty=problem.difficulty.value if hasattr(problem.difficulty, "value") else str(problem.difficulty),
                    tags=tag_names,
                    time_limit_ms=cp_meta.time_limit_ms,
                    memory_limit_mb=cp_meta.memory_limit_mb,
                    solved=(problem.id in solved_problem_ids),
                )
            )
        return summaries

    @classmethod
    async def get_cp_problem_detail(
        cls,
        db: AsyncSession,
        slug_or_id: str,
        user_id: Optional[str] = None,
    ) -> Optional[CPProblemDetail]:
        """Retrieves complete CP problem statement with input/output format and sample cases."""
        stmt = (
            select(Problem, CPProblemMetadata)
            .join(CPProblemMetadata, Problem.id == CPProblemMetadata.problem_id)
            .where(
                (Problem.slug == slug_or_id) | (Problem.id == slug_or_id),
                Problem.status == ContentStatus.PUBLISHED,
            )
            .options(
                selectinload(Problem.tags),
                selectinload(Problem.examples),
            )
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            return None

        problem, cp_meta = row

        is_solved = False
        if user_id:
            sub_stmt = select(func.count(Submission.id)).where(
                Submission.user_id == user_id,
                Submission.problem_id == problem.id,
                Submission.status == SubmissionStatus.ACCEPTED,
            )
            is_solved = bool((await db.execute(sub_stmt)).scalar() or 0)

        samples = []
        for ex in problem.examples:
            samples.append(
                CPSampleTestCase(
                    input=ex.input,
                    expected_output=ex.output,
                    explanation=ex.explanation,
                )
            )

        tag_names = [t.name for t in problem.tags] if problem.tags else []

        return CPProblemDetail(
            id=cp_meta.id,
            problem_id=problem.id,
            title=problem.title,
            slug=problem.slug,
            description=problem.statement,
            rating_band=cp_meta.rating_band,
            difficulty=problem.difficulty.value if hasattr(problem.difficulty, "value") else str(problem.difficulty),
            tags=tag_names,
            time_limit_ms=cp_meta.time_limit_ms,
            memory_limit_mb=cp_meta.memory_limit_mb,
            input_format=cp_meta.input_format,
            output_format=cp_meta.output_format,
            constraints=cp_meta.constraints,
            sample_cases=samples,
            editorial=cp_meta.editorial,
            solved=is_solved,
        )

    @classmethod
    async def get_user_profile(
        cls,
        db: AsyncSession,
        user_id: str,
    ) -> CPRatingProfile:
        """Retrieves user's competitive profile."""
        rating_obj = await cls.get_or_create_rating(db, user_id)
        user = await db.get(User, user_id)
        display_name = f"User_{user_id[:6]}"
        if user and hasattr(user, "email") and user.email:
            display_name = user.email.split("@")[0]

        return CPRatingProfile(
            user_id=user_id,
            display_name=display_name,
            current_rating=rating_obj.current_rating,
            peak_rating=rating_obj.peak_rating,
            contests_played=rating_obj.contests_played,
            contests_won=rating_obj.contests_won,
            problems_solved=rating_obj.problems_solved,
            rank_title=get_rank_title(rating_obj.current_rating),
        )

    @classmethod
    async def get_cp_leaderboard(
        cls,
        db: AsyncSession,
        limit: int = 50,
    ) -> CPLeaderboardResponse:
        """Returns competitive programming Elo leaderboard."""
        stmt = (
            select(CompetitiveRating, User)
            .join(User, CompetitiveRating.user_id == User.id)
            .order_by(CompetitiveRating.current_rating.desc(), CompetitiveRating.contests_won.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        rows = res.all()

        entries = []
        for rank, (rating_obj, user) in enumerate(rows, start=1):
            display_name = f"User_{user.id[:6]}"
            if user and hasattr(user, "email") and user.email:
                display_name = user.email.split("@")[0]

            entries.append(
                CPLeaderboardEntry(
                    rank=rank,
                    display_name=display_name,
                    current_rating=rating_obj.current_rating,
                    peak_rating=rating_obj.peak_rating,
                    contests_played=rating_obj.contests_played,
                    problems_solved=rating_obj.problems_solved,
                    rank_title=get_rank_title(rating_obj.current_rating),
                )
            )

        return CPLeaderboardResponse(
            total=len(entries),
            entries=entries,
        )
