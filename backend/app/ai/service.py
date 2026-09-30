"""High-Level AI Learning System Orchestration Service.

Integrates AI providers with database records, curriculum metadata,
progress tracking, mistake notebook patterns, and security guardrails.
"""

from datetime import datetime, timezone
import logging
import time
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.ai.providers import get_ai_provider
from backend.app.ai.security.prompt_guard import PromptGuard
from backend.app.ai.usage import AIUsageTracker
from backend.app.core.config import settings
from backend.app.models.ai import AIConversation, AIHintUsage, AIMessage, AIRequestType
from backend.app.models.content import Problem, Topic, ContentStatus
from backend.app.models.progress import (
    Mistake,
    ProblemProgressStatus,
    RevisionItem,
    RevisionSchedule,
    Submission,
    UserProblemProgress,
)

from backend.app.models.user import User
from backend.app.schemas.ai import (
    AIUsageSummaryResponse,
    ComplexityRequest,
    ComplexityResponse,
    ExplainRequest,
    ExplainResponse,
    HintRequest,
    HintResponse,
    PatternRequest,
    PatternResponse,
    RecommendationItem,
    RecommendationResponse,
    TutorRequest,
    TutorResponse,
    WeakTopicItem,
)

logger = logging.getLogger(__name__)


class AIService:
    """Orchestrates AI learning assistance with strict server-side authorization and data isolation."""

    @staticmethod
    async def _enforce_quota_and_track(
        db: AsyncSession,
        user: User,
        request_type: str,
    ) -> None:
        """Enforces daily quota limit server-side."""
        is_premium = bool(getattr(user, "is_premium", False))
        can_proceed, daily_used, remaining = await AIUsageTracker.check_quota(db, user.id, is_premium)
        if not can_proceed:
            tier_name = "Premium" if is_premium else "Free"
            limit = (
                settings.AI_PREMIUM_TIER_DAILY_LIMIT
                if is_premium
                else settings.AI_FREE_TIER_DAILY_LIMIT
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily AI request quota reached ({daily_used}/{limit} requests for {tier_name} tier). Please try again tomorrow or upgrade your plan.",
            )

    @staticmethod
    async def ask_tutor(
        db: AsyncSession,
        user: User,
        request: TutorRequest,
    ) -> TutorResponse:
        """Processes an educational inquiry to the AI Tutor."""
        await AIService._enforce_quota_and_track(db, user, AIRequestType.TUTOR.value)

        problem_title = None
        problem_desc = None
        if request.problem_id:
            prob_stmt = select(Problem).where(
                or_(Problem.id == request.problem_id, Problem.slug == request.problem_id),
                Problem.status == ContentStatus.PUBLISHED,
            )
            prob_res = await db.execute(prob_stmt)
            problem = prob_res.scalars().first()
            if problem:
                problem_title = problem.title
                problem_desc = problem.statement

        start_time = time.monotonic()
        provider = get_ai_provider()
        success = True
        err_msg = None

        try:
            response = await provider.tutor(
                request,
                problem_title=problem_title,
                problem_description=problem_desc,
            )


            # Persist message to conversation if conversation_id provided or new
            conv_id = request.conversation_id
            if not conv_id:
                conv = AIConversation(
                    user_id=user.id,
                    problem_id=request.problem_id,
                    lesson_id=request.lesson_id,
                    title=f"Question: {request.question[:40]}...",
                )
                db.add(conv)
                await db.commit()
                await db.refresh(conv)
                conv_id = conv.id

            # Save user query & assistant answer
            user_msg = AIMessage(conversation_id=conv_id, role="user", content=request.question)
            assistant_msg = AIMessage(
                conversation_id=conv_id,
                role="assistant",
                content=f"{response.explanation}\n\nKey Idea: {response.key_idea}",
            )
            db.add_all([user_msg, assistant_msg])
            await db.commit()

            response.conversation_id = conv_id
            return response

        except Exception as e:
            success = False
            err_msg = str(e)
            logger.error("AI Tutor call failed: %s", err_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI Tutor service encountered a temporary error. Please try again.",
            )
        finally:
            latency = int((time.monotonic() - start_time) * 1000)
            await AIUsageTracker.record_usage(
                db=db,
                user_id=user.id,
                request_type=AIRequestType.TUTOR.value,
                provider=provider.get_diagnostics().get("provider", "mock"),
                model=provider.get_diagnostics().get("model", "mock-dsa-model-v1"),
                latency_ms=latency,
                success=success,
                error_message=err_msg,
            )

    @staticmethod
    async def get_progressive_hint(
        db: AsyncSession,
        user: User,
        request: HintRequest,
    ) -> HintResponse:
        """Fetches or generates a tiered progressive hint."""
        await AIService._enforce_quota_and_track(db, user, AIRequestType.HINT.value)

        # 1. Fetch problem metadata (NEVER expose hidden test cases!)
        stmt = (
            select(Problem)
            .where(
                or_(Problem.id == request.problem_id, Problem.slug == request.problem_id),
                Problem.status == ContentStatus.PUBLISHED,
            )
            .options(selectinload(Problem.hints))
        )
        result = await db.execute(stmt)
        problem = result.scalars().first()

        if not problem:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Problem '{request.problem_id}' not found.",
            )

        # Record hint usage in AIHintUsage
        try:
            count_stmt = select(func.count(AIHintUsage.id)).where(
                AIHintUsage.user_id == user.id,
                AIHintUsage.problem_id == problem.id,
            )
            prev_hints_count = (await db.execute(count_stmt)).scalar_one_or_none() or 0
            new_hints_count = prev_hints_count + 1

            hint_log = AIHintUsage(
                user_id=user.id,
                problem_id=problem.id,
                hint_level=request.hint_level,
                timestamp=datetime.now(timezone.utc),
                number_of_hints_used=new_hints_count,
            )
            db.add(hint_log)
            await db.commit()
        except Exception as log_err:
            logger.warning("Could not record AIHintUsage: %s", log_err)
            await db.rollback()

        # Extract pre-authored hint contents sorted by order
        sorted_hints = [
            h.content for h in sorted(problem.hints, key=lambda x: x.hint_number)
        ]

        start_time = time.monotonic()
        provider = get_ai_provider()
        success = True
        err_msg = None

        try:
            hint_res = await provider.hint(
                request=request,
                problem_title=problem.title,
                problem_description=problem.statement,
                problem_hints=sorted_hints,
            )
            return hint_res

        except Exception as e:
            success = False
            err_msg = str(e)
            logger.error("AI Hint call failed: %s", err_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Hint generation service temporarily unavailable.",
            )
        finally:
            latency = int((time.monotonic() - start_time) * 1000)
            await AIUsageTracker.record_usage(
                db=db,
                user_id=user.id,
                request_type=AIRequestType.HINT.value,
                provider=provider.get_diagnostics().get("provider", "mock"),
                model=provider.get_diagnostics().get("model", "mock-dsa-model-v1"),
                latency_ms=latency,
                success=success,
                error_message=err_msg,
            )

    @staticmethod
    async def explain_content(
        db: AsyncSession,
        user: User,
        request: ExplainRequest,
    ) -> ExplainResponse:
        """Generates conceptual, algorithmic, or diagnostic error explanation."""
        await AIService._enforce_quota_and_track(db, user, AIRequestType.EXPLAIN.value)

        problem_title = None
        if request.problem_id:
            p_stmt = select(Problem.title).where(
                or_(Problem.id == request.problem_id, Problem.slug == request.problem_id)
            )
            prob_res = await db.execute(p_stmt)
            problem_title = prob_res.scalar_one_or_none()

        submission_context = ""
        if request.submission_id:
            sub_stmt = (
                select(Submission)
                .where(or_(Submission.id == request.submission_id, Submission.public_id == request.submission_id))
                .options(selectinload(Submission.problem), selectinload(Submission.result))
            )
            sub_res = await db.execute(sub_stmt)
            sub = sub_res.scalars().first()
            if sub:
                if not problem_title and sub.problem:
                    problem_title = sub.problem.title
                verdict_str = (
                    sub.result.verdict.value
                    if (sub.result and hasattr(sub.result.verdict, "value"))
                    else str(sub.status.value if hasattr(sub.status, "value") else sub.status)
                )
                comp_out = (sub.result.compiler_output_safe or "") if sub.result else ""
                run_out = (sub.result.runtime_output_safe or "") if sub.result else ""
                submission_context = (
                    f"\n[Execution Diagnostics for Submission {sub.public_id}]\n"
                    f"Verdict: {verdict_str}\n"
                    f"Language: {sub.language}\n"
                    f"Compiler Diagnostic: {comp_out or 'None'}\n"
                    f"Runtime Diagnostic: {run_out or 'None'}\n"
                    f"Source Code:\n{sub.source_code[:4000]}"
                )

        start_time = time.monotonic()
        provider = get_ai_provider()
        success = True
        err_msg = None

        try:
            effective_request = request
            if submission_context:
                effective_request = request.model_copy(
                    update={"context_text": f"{request.context_text}\n{submission_context}"}
                )
            return await provider.explain(effective_request, problem_title=problem_title)
        except Exception as e:
            success = False
            err_msg = str(e)
            logger.error("AI Explain call failed: %s", err_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Explanation service temporarily unavailable.",
            )
        finally:
            latency = int((time.monotonic() - start_time) * 1000)
            await AIUsageTracker.record_usage(
                db=db,
                user_id=user.id,
                request_type=AIRequestType.EXPLAIN.value,
                provider=provider.get_diagnostics().get("provider", "mock"),
                model=provider.get_diagnostics().get("model", "mock-dsa-model-v1"),
                latency_ms=latency,
                success=success,
                error_message=err_msg,
            )

    @staticmethod
    async def analyze_complexity(
        db: AsyncSession,
        user: User,
        request: ComplexityRequest,
    ) -> ComplexityResponse:
        """Performs Big-O time and space complexity evaluation."""
        await AIService._enforce_quota_and_track(db, user, AIRequestType.COMPLEXITY.value)

        start_time = time.monotonic()
        provider = get_ai_provider()
        success = True
        err_msg = None

        try:
            return await provider.complexity(request)
        except Exception as e:
            success = False
            err_msg = str(e)
            logger.error("AI Complexity call failed: %s", err_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Complexity analysis service temporarily unavailable.",
            )
        finally:
            latency = int((time.monotonic() - start_time) * 1000)
            await AIUsageTracker.record_usage(
                db=db,
                user_id=user.id,
                request_type=AIRequestType.COMPLEXITY.value,
                provider=provider.get_diagnostics().get("provider", "mock"),
                model=provider.get_diagnostics().get("model", "mock-dsa-model-v1"),
                latency_ms=latency,
                success=success,
                error_message=err_msg,
            )

    @staticmethod
    async def detect_pattern(
        db: AsyncSession,
        user: User,
        request: PatternRequest,
    ) -> PatternResponse:
        """Identifies algorithmic patterns from code or problem descriptions."""
        await AIService._enforce_quota_and_track(db, user, AIRequestType.PATTERN.value)

        problem_title = None
        effective_request = request
        if request.problem_id:
            p_stmt = select(Problem).where(
                or_(Problem.id == request.problem_id, Problem.slug == request.problem_id)
            )
            prob_res = await db.execute(p_stmt)
            problem = prob_res.scalars().first()
            if problem:
                problem_title = problem.title
                if not request.problem_description:
                    effective_request = request.model_copy(update={"problem_description": problem.statement})

        start_time = time.monotonic()
        provider = get_ai_provider()
        success = True
        err_msg = None

        try:
            return await provider.pattern(effective_request, problem_title=problem_title)
        except Exception as e:
            success = False
            err_msg = str(e)
            logger.error("AI Pattern call failed: %s", err_msg)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Pattern detection service temporarily unavailable.",
            )
        finally:
            latency = int((time.monotonic() - start_time) * 1000)
            await AIUsageTracker.record_usage(
                db=db,
                user_id=user.id,
                request_type=AIRequestType.PATTERN.value,
                provider=provider.get_diagnostics().get("provider", "mock"),
                model=provider.get_diagnostics().get("model", "mock-dsa-model-v1"),
                latency_ms=latency,
                success=success,
                error_message=err_msg,
            )

    @staticmethod
    async def get_personalized_recommendations(
        db: AsyncSession,
        user: User,
    ) -> RecommendationResponse:
        """Synthesizes recommendations using actual Phase 4 progress, mistakes, and revision data."""
        # 1. Fetch user progress records
        prog_stmt = select(UserProblemProgress).where(UserProblemProgress.user_id == user.id)
        prog_res = await db.execute(prog_stmt)
        progress_items = prog_res.scalars().all()

        # 2. Fetch user mistakes
        mistake_stmt = select(Mistake).where(Mistake.user_id == user.id)
        mistake_res = await db.execute(mistake_stmt)
        mistakes = mistake_res.scalars().all()

        # 3. Fetch due revision items
        now_utc = datetime.now(timezone.utc)
        rev_stmt = (
            select(RevisionItem)
            .join(RevisionSchedule, RevisionItem.id == RevisionSchedule.revision_item_id)
            .where(
                RevisionItem.user_id == user.id,
                RevisionItem.is_active.is_(True),
                RevisionSchedule.due_at <= now_utc,
            )
        )
        rev_res = await db.execute(rev_stmt)
        due_revisions = rev_res.scalars().all()


        has_data = len(progress_items) > 0 or len(mistakes) > 0

        # If brand-new learner, return clear "insufficient data" state with curriculum entry points
        if not has_data:
            starter_stmt = (
                select(Problem)
                .where(Problem.status == ContentStatus.PUBLISHED)
                .order_by(Problem.created_at.asc())
                .limit(3)
            )
            starter_res = await db.execute(starter_stmt)
            starters = starter_res.scalars().all()

            recommendations = [
                RecommendationItem(
                    topic_id="starter-fundamentals",
                    topic_title="Foundations & Arrays",
                    problem_id=p.id,
                    problem_title=p.title,
                    difficulty=str(p.difficulty.value if hasattr(p.difficulty, "value") else p.difficulty),
                    reason="Begin your learning journey with introductory array and string challenges.",
                    priority="HIGH",
                    estimated_effort_minutes=20,
                    related_pattern="Array Iteration",
                )
                for p in starters
            ]

            return RecommendationResponse(
                has_sufficient_data=False,
                summary_insight="You haven't completed any problem attempts or documented mistakes yet. Here are recommended foundational problems to start with.",
                recommendations=recommendations,
                weak_topics=[],
                pending_revisions_count=0,
            )

        # Process real progress data
        unsolved_problems = [p for p in progress_items if p.status == ProblemProgressStatus.ATTEMPTED]
        solved_count = len([p for p in progress_items if p.status == ProblemProgressStatus.SOLVED])

        # Analyze mistake patterns
        mistake_type_counts: dict = {}
        for m in mistakes:
            m_type = m.mistake_type.value if hasattr(m.mistake_type, "value") else str(m.mistake_type)
            mistake_type_counts[m_type] = mistake_type_counts.get(m_type, 0) + 1

        weak_topics = []
        if mistake_type_counts:
            most_frequent_err = max(mistake_type_counts.items(), key=lambda x: x[1])
            weak_topics.append(WeakTopicItem(
                topic_id="cognitive-focus",
                topic_title=f"Common Error: {most_frequent_err[0]}",
                mistake_count=most_frequent_err[1],
                unsolved_attempts=len(unsolved_problems),
                suggested_action=f"Review logic handling for {most_frequent_err[0]} before submitting.",
            ))

        # Build recommendations
        recs: List[RecommendationItem] = []

        # A. Priority 1: Unsolved attempted problems
        for unp in unsolved_problems[:2]:
            prob_stmt = select(Problem).where(Problem.id == unp.problem_id)
            p_obj = (await db.execute(prob_stmt)).scalars().first()
            if p_obj:
                recs.append(RecommendationItem(
                    topic_id="active-challenges",
                    topic_title="Attempted Problems",
                    problem_id=p_obj.id,
                    problem_title=p_obj.title,
                    difficulty=str(p_obj.difficulty.value if hasattr(p_obj.difficulty, "value") else p_obj.difficulty),
                    reason=f"You previously attempted this problem ({unp.attempts_count} attempts) but have not solved it yet. Use hints to complete it.",
                    priority="HIGH",
                    estimated_effort_minutes=25,
                    related_pattern=None,
                ))

        # B. Priority 2: Next published problem to advance difficulty
        next_prob_stmt = (
            select(Problem)
            .where(
                Problem.status == ContentStatus.PUBLISHED,
                Problem.id.notin_([p.problem_id for p in progress_items if p.status == ProblemProgressStatus.SOLVED]),
            )
            .order_by(Problem.display_order.asc())
            .limit(2)
        )
        next_probs = (await db.execute(next_prob_stmt)).scalars().all()
        for np in next_probs:
            if not any(r.problem_id == np.id for r in recs):
                recs.append(RecommendationItem(
                    topic_id="curriculum-advance",
                    topic_title="Curriculum Progression",
                    problem_id=np.id,
                    problem_title=np.title,
                    difficulty=str(np.difficulty.value if hasattr(np.difficulty, "value") else np.difficulty),
                    reason="Recommended next step in your curriculum pathway.",
                    priority="MEDIUM",
                    estimated_effort_minutes=30,
                    related_pattern=None,
                ))

        insight = (
            f"You have solved {solved_count} problem(s) and recorded {len(mistakes)} mistake insight(s). "
            f"There are {len(due_revisions)} items currently due for spaced repetition."
        )

        return RecommendationResponse(
            has_sufficient_data=True,
            summary_insight=insight,
            recommendations=recs,
            weak_topics=weak_topics,
            pending_revisions_count=len(due_revisions),
        )

    @staticmethod
    async def get_usage_summary(
        db: AsyncSession,
        user: User,
    ) -> AIUsageSummaryResponse:
        """Returns the current daily AI quota usage and limits."""
        is_premium = bool(getattr(user, "is_premium", False))
        can_proceed, daily_used, remaining = await AIUsageTracker.check_quota(db, user.id, is_premium)
        provider = get_ai_provider()
        diag = provider.get_diagnostics()

        total_quota = (
            settings.AI_PREMIUM_TIER_DAILY_LIMIT
            if is_premium
            else settings.AI_FREE_TIER_DAILY_LIMIT
        )

        return AIUsageSummaryResponse(
            daily_quota=total_quota,
            daily_used=daily_used,
            daily_remaining=remaining,
            is_premium=is_premium,
            provider=diag.get("provider", "mock"),
            model=diag.get("model", "mock-dsa-model-v1"),
            can_request=can_proceed,
        )
