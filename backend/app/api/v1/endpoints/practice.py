"""Practice Engine API Endpoints.

Handles:
- Interactive practice session lifecycle (start, step problem, complete)
- Deterministic multi-factor problem recommendations
- AI-assisted pedagogical explanation of problem selection
- Daily Challenge status and idempotent reward claiming
- Paginated practice session history
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_current_user_optional, get_db
from backend.app.models.content import ContentStatus, Problem
from backend.app.models.gamification import PracticeSession
from backend.app.models.progress import ProblemProgressStatus, UserProblemProgress
from backend.app.models.user import User
from backend.app.schemas.gamification import (
    ClaimDailyRewardResponse,
    CreatePracticeSessionRequest,
    DailyChallengeResponse,
    ExplainRecommendationResponse,
    PracticeRecommendationsResponse,
    PracticeSessionProblemResponse,
    PracticeSessionResponse,
    RecommendationItemResponse,
    RecordProblemResultRequest,
    RecordProblemResultResponse,
)
from backend.app.services.gamification.daily_challenge_service import DailyChallengeService
from backend.app.services.gamification.practice_session_service import PracticeSessionService
from backend.app.services.gamification.recommendation_service import IntelligentProblemSelector
from backend.app.services.gamification.streak_service import StreakService

logger = logging.getLogger(__name__)

router = APIRouter()


def _format_session_response(session: PracticeSession) -> PracticeSessionResponse:
    """Helper mapping PracticeSession model to response schema."""
    problems_dto = [
        PracticeSessionProblemResponse(
            id=p.id,
            problem_id=p.problem_id,
            sequence=p.sequence,
            title=p.problem.title if p.problem else "Coding Problem",
            slug=p.problem.slug if p.problem else "",
            difficulty=p.problem.difficulty.value if p.problem else "EASY",
            attempted=p.attempted,
            solved=p.solved,
            time_spent_seconds=p.time_spent_seconds,
        )
        for p in session.session_problems
    ]
    return PracticeSessionResponse(
        id=session.id,
        user_id=session.user_id,
        mode=session.mode,
        status=session.status,
        target_count=session.target_count,
        completed_count=session.completed_count,
        solved_count=session.solved_count,
        xp_earned=session.xp_earned,
        accuracy=session.accuracy,
        duration_seconds=session.duration_seconds,
        started_at=session.started_at,
        completed_at=session.completed_at,
        problems=problems_dto,
    )


# ─────────────────────────────────────────────────────────────
# 1. PRACTICE SESSIONS
# ─────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=PracticeSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_practice_session(
    payload: CreatePracticeSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initializes a new practice session with recommended problems."""
    session = await PracticeSessionService.create_session(
        db=db,
        user=current_user,
        mode=payload.mode,
        topic_id=payload.topic_id,
        pattern_id=payload.pattern_id,
        difficulty=payload.difficulty,
        target_count=payload.target_count,
    )
    # Reload with relationships
    loaded_session = await PracticeSessionService.get_session(db, session.id, current_user.id)
    return _format_session_response(loaded_session)


@router.get("/sessions/{session_id}", response_model=PracticeSessionResponse)
async def get_practice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves practice session state with strict IDOR ownership enforcement."""
    session = await PracticeSessionService.get_session(db, session_id, current_user.id)
    return _format_session_response(session)


@router.post("/sessions/{session_id}/problem/{problem_id}/result", response_model=RecordProblemResultResponse)
async def record_practice_problem_result(
    session_id: str,
    problem_id: str,
    payload: RecordProblemResultRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Records the outcome of a problem attempted within the session."""
    session, xp_awarded = await PracticeSessionService.record_problem_result(
        db=db,
        user=current_user,
        session_id=session_id,
        problem_id=problem_id,
        solved=payload.solved,
        time_spent_seconds=payload.time_spent_seconds,
        submission_id=payload.submission_id,
    )
    return RecordProblemResultResponse(
        session_id=session.id,
        problem_id=problem_id,
        solved=payload.solved,
        xp_awarded=xp_awarded,
        accuracy=session.accuracy,
    )


@router.post("/sessions/{session_id}/complete", response_model=PracticeSessionResponse)
async def complete_practice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalizes an active practice session and calculates authoritative accuracy and rewards."""
    session = await PracticeSessionService.complete_session(db, current_user, session_id)
    loaded_session = await PracticeSessionService.get_session(db, session.id, current_user.id)
    return _format_session_response(loaded_session)


@router.get("/history", response_model=List[PracticeSessionResponse])
async def get_practice_history(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns paginated historical practice sessions for the logged in learner."""
    sessions, _ = await PracticeSessionService.get_user_session_history(
        db=db, user_id=current_user.id, limit=limit, offset=offset
    )
    return [_format_session_response(s) for s in sessions]


# ─────────────────────────────────────────────────────────────
# 2. RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────

@router.get("/recommendations", response_model=PracticeRecommendationsResponse)
async def get_practice_recommendations(
    mode: str = Query("QUICK", description="Category mode: QUICK, WEAK_AREA, MISTAKES, REVISION"),
    limit: int = Query(5, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generates intelligent problem recommendations using deterministic multi-factor scoring."""
    candidates = await IntelligentProblemSelector.select_practice_problems(
        db=db,
        user=current_user,
        mode=mode,
        limit=limit,
    )
    dto_list = [
        RecommendationItemResponse(
            problem_id=c.problem_id,
            slug=c.slug,
            title=c.title,
            difficulty=c.difficulty,
            score=c.score,
            reasons=c.reasons,
            category=c.category,
        )
        for c in candidates
    ]
    return PracticeRecommendationsResponse(mode=mode, recommendations=dto_list)


@router.get("/recommendations/explain/{problem_id}", response_model=ExplainRecommendationResponse)
async def explain_problem_recommendation(
    problem_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Provides a natural-language explanation of why this specific problem was selected."""
    stmt = select(Problem).where(Problem.id == problem_id, Problem.status == ContentStatus.PUBLISHED)
    problem = (await db.execute(stmt)).scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found.")

    # Check user context
    prog_stmt = select(UserProblemProgress).where(
        UserProblemProgress.user_id == current_user.id,
        UserProblemProgress.problem_id == problem_id,
    )
    prog = (await db.execute(prog_stmt)).scalar_one_or_none()

    factors: List[str] = [
        f"Difficulty: {problem.difficulty.value} tier calibrated to your current problem-solving momentum.",
        "Algorithmic reinforcement: Promotes mastery of core constraints and invariants.",
    ]

    if prog and prog.status == ProblemProgressStatus.ATTEMPTED:
        factors.append("Recent incomplete attempt detected. Recommended to achieve full solution acceptance.")
    elif prog and prog.status == ProblemProgressStatus.SOLVED:
        factors.append("Previously solved. Recommended for spaced repetition memory consolidation.")
    else:
        factors.append("Fresh curriculum challenge designed to broaden your algorithmic pattern recognition.")

    explanation = (
        f"'{problem.title}' was recommended based on your recent practice trends. "
        f"Solving this {problem.difficulty.value} problem will strengthen your understanding of algorithmic trade-offs "
        f"and prepare you for related data structure challenges."
    )

    return ExplainRecommendationResponse(
        problem_id=problem.id,
        title=problem.title,
        explanation=explanation,
        pedagogical_factors=factors,
    )


# ─────────────────────────────────────────────────────────────
# 3. DAILY CHALLENGE
# ─────────────────────────────────────────────────────────────

@router.get("/daily", response_model=DailyChallengeResponse)
async def get_daily_challenge(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves today's calendar daily challenge and user completion status (supports guests)."""
    today_str = StreakService.get_today_str()
    challenge = await DailyChallengeService.get_or_create_daily_challenge(db, today_str)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No daily challenge configured for today.",
        )

    # Check user solve status if authenticated
    is_solved = False
    first_attempt = False
    has_claimed = False
    can_claim = False
    xp_awarded = 0
    user_challenge = None

    if current_user:
        prog_stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == current_user.id,
            UserProblemProgress.problem_id == challenge.problem_id,
        )
        user_prog = (await db.execute(prog_stmt)).scalar_one_or_none()
        is_solved = bool(user_prog and user_prog.status == ProblemProgressStatus.SOLVED)
        first_attempt = bool(user_prog and user_prog.attempts_count == 1)

        # Check if reward claimed
        user_challenge = await DailyChallengeService.get_user_challenge_status(db, current_user.id, challenge)
        has_claimed = bool(user_challenge and user_challenge.solved)
        can_claim = is_solved and not has_claimed
        xp_awarded = user_challenge.xp_awarded if user_challenge else 0

    problem = await db.get(Problem, challenge.problem_id)
    return DailyChallengeResponse(
        id=challenge.id,
        challenge_date=challenge.challenge_date,
        problem_id=challenge.problem_id,
        problem_title=problem.title if problem else "Daily Problem",
        problem_slug=problem.slug if problem else "",
        difficulty=problem.difficulty.value if problem else "EASY",
        xp_reward=challenge.xp_reward,
        bonus_xp=challenge.bonus_xp,
        solved=has_claimed or is_solved,
        first_attempt_solve=first_attempt,
        xp_awarded=user_challenge.xp_awarded if user_challenge else 0,
        can_claim=can_claim,
    )


@router.post("/daily/claim", response_model=ClaimDailyRewardResponse)
async def claim_daily_challenge_reward(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validates solution and claims the daily challenge XP reward idempotently."""
    today_str = StreakService.get_today_str()
    success, xp_awarded, msg = await DailyChallengeService.claim_daily_challenge_reward(
        db=db, user_id=current_user.id, date_str=today_str
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return ClaimDailyRewardResponse(
        success=True,
        xp_awarded=xp_awarded,
        message=msg,
    )
