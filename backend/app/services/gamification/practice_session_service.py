"""Practice Session Lifecycle Service.

Orchestrates multi-problem interactive practice sessions, problem sequencing,
accuracy calculation, XP rewards, rating progression, and achievement unlocks.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.gamification import (
    PracticeMode,
    PracticeSession,
    PracticeSessionProblem,
    PracticeSessionStatus,
)
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository
from backend.app.services.gamification.achievement_service import AchievementService
from backend.app.services.gamification.adaptive_difficulty_service import (
    AdaptiveDifficultyService,
)
from backend.app.services.gamification.rating_service import RatingService
from backend.app.services.gamification.recommendation_service import (
    IntelligentProblemSelector,
)
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XP_REWARDS, XPService

logger = logging.getLogger(__name__)


class PracticeSessionService:
    """Manages active and historical learner practice sessions."""

    @classmethod
    async def create_session(
        cls,
        db: AsyncSession,
        user: User,
        mode: str = "QUICK",
        topic_id: str | None = None,
        pattern_id: str | None = None,
        difficulty: str | None = None,
        target_count: int = 3,
    ) -> PracticeSession:
        """Initializes a new practice session with intelligently selected problems."""
        target_count = min(
            max(1, target_count), 10
        )  # Bound target count between 1 and 10

        # Mode validation
        try:
            mode_enum = PracticeMode(mode.upper())
        except ValueError:
            mode_enum = PracticeMode.QUICK

        # Premium gating on advanced adaptive/mistake modes
        if mode_enum in (PracticeMode.WEAK_AREA, PracticeMode.MISTAKES):
            is_premium = await UserRepository(db).has_active_premium(user.id)
            if not is_premium:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"The {mode_enum.value} practice mode requires a Pro tier subscription.",
                )

        # Determine adaptive difficulty if not explicitly passed
        chosen_diff = difficulty
        if not chosen_diff:
            (
                chosen_diff,
                _,
            ) = await AdaptiveDifficultyService.determine_adaptive_difficulty(
                db=db, user_id=user.id
            )

        # Select candidate problems
        candidates = await IntelligentProblemSelector.select_practice_problems(
            db=db,
            user=user,
            mode=mode_enum.value,
            topic_id=topic_id,
            pattern_id=pattern_id,
            preferred_difficulty=chosen_diff,
            limit=target_count,
        )

        now = datetime.now(timezone.utc)
        session = PracticeSession(
            user_id=user.id,
            mode=mode_enum.value,
            topic_id=topic_id,
            pattern_id=pattern_id,
            difficulty=chosen_diff,
            status=PracticeSessionStatus.IN_PROGRESS.value,
            target_count=len(candidates) if candidates else target_count,
            completed_count=0,
            solved_count=0,
            xp_earned=0,
            accuracy=0.0,
            duration_seconds=0,
            started_at=now,
        )
        db.add(session)
        await db.flush()

        for idx, cand in enumerate(candidates, start=1):
            sess_prob = PracticeSessionProblem(
                session_id=session.id,
                problem_id=cand.problem_id,
                sequence=idx,
                served_at=now,
                attempted=False,
                solved=False,
                time_spent_seconds=0,
            )
            db.add(sess_prob)

        await db.flush()
        logger.info(
            f"Created PracticeSession {session.id} ({session.mode}) with {len(candidates)} problems for user {user.id}"
        )
        return session

    @classmethod
    async def get_session(
        cls,
        db: AsyncSession,
        session_id: str,
        user_id: str,
    ) -> PracticeSession:
        """Retrieves a practice session with strict user IDOR validation."""
        stmt = (
            select(PracticeSession)
            .where(PracticeSession.id == session_id)
            .options(
                selectinload(PracticeSession.session_problems).selectinload(
                    PracticeSessionProblem.problem
                ),
                selectinload(PracticeSession.topic),
                selectinload(PracticeSession.pattern),
            )
        )
        session: PracticeSession | None = (await db.execute(stmt)).scalar_one_or_none()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Practice session not found.",
            )

        # IDOR Protection
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You do not own this practice session.",
            )

        return session

    @classmethod
    async def record_problem_result(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
        problem_id: str,
        solved: bool,
        time_spent_seconds: int,
        submission_id: str | None = None,
    ) -> tuple[PracticeSession, int]:
        """Records the outcome of a problem attempted within the session.

        Returns:
            Tuple[PracticeSession, xp_awarded_for_solve]
        """
        session = await cls.get_session(db, session_id, user.id)

        if session.status != PracticeSessionStatus.IN_PROGRESS.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot record result on session with status '{session.status}'.",
            )

        # Find matching problem in session
        sess_prob = next(
            (p for p in session.session_problems if p.problem_id == problem_id), None
        )
        if not sess_prob:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem does not belong to this practice session.",
            )

        sess_prob.attempted = True
        sess_prob.solved = solved
        sess_prob.time_spent_seconds = max(0, time_spent_seconds)
        if submission_id:
            sess_prob.submission_id = submission_id

        xp_awarded = 0
        if solved:
            # Determine problem difficulty reward
            prob = sess_prob.problem
            diff_key = (
                f"PROBLEM_SOLVE_{prob.difficulty.value.upper()}"
                if prob
                else "PROBLEM_SOLVE_EASY"
            )
            amount = XP_REWARDS.get(diff_key, 20)

            # Idempotently credit solve XP
            _, is_new, _ = await XPService.record_xp_event(
                db=db,
                user_id=user.id,
                event_type="PROBLEM_SOLVE",
                source_id=f"session:{session.id}:prob:{problem_id}",
                amount=amount,
                metadata={"difficulty": prob.difficulty.value if prob else "EASY"},
            )
            if is_new:
                xp_awarded = amount
                session.xp_earned += amount

            # Record streak activity
            await StreakService.record_qualifying_activity(
                db=db, user_id=user.id, activity_type="PROBLEM_SOLVE"
            )

            # Adjust skill rating
            if prob:
                await RatingService.record_problem_solve(
                    db=db,
                    user_id=user.id,
                    problem_id=prob.id,
                    difficulty=prob.difficulty.value,
                )

        await db.flush()
        return session, xp_awarded

    @classmethod
    async def complete_session(
        cls,
        db: AsyncSession,
        user: User,
        session_id: str,
    ) -> PracticeSession:
        """Finalizes an active practice session and computes authoritative accuracy and rewards."""
        session = await cls.get_session(db, session_id, user.id)

        if session.status == PracticeSessionStatus.COMPLETED.value:
            return session

        now = datetime.now(timezone.utc)
        session.completed_at = now
        session.status = PracticeSessionStatus.COMPLETED.value

        # Calculate statistics from problems
        probs = session.session_problems
        completed_count = sum(1 for p in probs if p.attempted)
        solved_count = sum(1 for p in probs if p.solved)
        total_time = sum(p.time_spent_seconds for p in probs)

        session.completed_count = completed_count
        session.solved_count = solved_count
        session.accuracy = round((solved_count / len(probs)) if probs else 0.0, 2)
        session.duration_seconds = total_time or int(
            (now - session.started_at).total_seconds()
        )

        # Award session completion bonus XP
        completion_xp = XP_REWARDS.get("PRACTICE_SESSION_COMPLETE", 30)
        _, is_new, _ = await XPService.record_xp_event(
            db=db,
            user_id=user.id,
            event_type="PRACTICE_SESSION_COMPLETE",
            source_id=f"session_complete:{session.id}",
            amount=completion_xp,
            metadata={"session_id": session.id, "accuracy": session.accuracy},
        )
        if is_new:
            session.xp_earned += completion_xp

        # Rating bonus for high accuracy
        await RatingService.record_session_completion(
            db=db, user_id=user.id, session_id=session.id, accuracy=session.accuracy
        )

        # Evaluate achievements
        await AchievementService.evaluate_achievements(db, user.id)

        await db.flush()
        logger.info(
            f"PracticeSession {session.id} finalized. Solved: {solved_count}/{len(probs)}, Accuracy: {session.accuracy * 100}%"
        )
        return session

    @classmethod
    async def get_user_session_history(
        cls,
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[PracticeSession], int]:
        """Returns paginated practice sessions for the specified user."""
        limit = min(max(1, limit), 50)
        offset = max(0, offset)

        count_stmt = select(func.count(PracticeSession.id)).where(
            PracticeSession.user_id == user_id
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(PracticeSession)
            .where(PracticeSession.user_id == user_id)
            .options(
                selectinload(PracticeSession.session_problems).selectinload(
                    PracticeSessionProblem.problem
                ),
                selectinload(PracticeSession.topic),
                selectinload(PracticeSession.pattern),
            )
            .order_by(desc(PracticeSession.created_at))
            .limit(limit)
            .offset(offset)
        )
        sessions: list[Any] = list((await db.execute(stmt)).scalars().all())
        return sessions, total
