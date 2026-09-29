"""Intelligent Problem Selection and Practice Recommendation Engine.

Computes multi-factor deterministic candidate scores:
CandidateScore = TopicNeed + PatternNeed + RevisionPriority + MistakePriority + DifficultyFit + Freshness

Strictly filters:
- Unpublished problems
- Inaccessible premium problems for Free tier users
- Already solved problems (except in REVISION mode)
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.content import (
    ContentAccessLevel,
    ContentStatus,
    Problem,
    ProblemDifficulty,
)
from backend.app.models.progress import (
    Mistake,
    ProblemProgressStatus,
    RevisionItem,
    RevisionSchedule,
    UserProblemProgress,
)
from backend.app.models.user import User
from backend.app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)


class ScoredProblemCandidate(BaseModel):
    """Candidate problem enriched with deterministic scoring rationale."""
    problem_id: str
    slug: str
    title: str
    difficulty: str
    topic_id: Optional[str]
    score: float
    reasons: List[str]
    category: str


class IntelligentProblemSelector:
    """Selects and ranks pedagogical practice problems deterministically."""

    @classmethod
    async def select_practice_problems(
        cls,
        db: AsyncSession,
        user: User,
        mode: str = "QUICK",
        topic_id: Optional[str] = None,
        pattern_id: Optional[str] = None,
        preferred_difficulty: Optional[str] = None,
        limit: int = 3,
    ) -> List[ScoredProblemCandidate]:
        """Selects up to `limit` optimal candidate problems tailored to learner state."""
        # 1. Check user premium entitlement
        is_premium = await UserRepository(db).has_active_premium(user.id)

        # 2. Query all published problems
        query = (
            select(Problem)
            .where(Problem.status == ContentStatus.PUBLISHED)
            .options(
                selectinload(Problem.patterns),
                selectinload(Problem.tags),
            )
        )
        if not is_premium:
            query = query.where(Problem.access_level == ContentAccessLevel.FREE)

        if topic_id:
            query = query.where(Problem.topic_id == topic_id)

        all_problems = (await db.execute(query)).scalars().all()
        if not all_problems:
            return []

        # 3. Gather learner context
        # Solved problems
        prog_stmt = select(UserProblemProgress).where(UserProblemProgress.user_id == user.id)
        user_progress_list = (await db.execute(prog_stmt)).scalars().all()
        solved_ids: Set[str] = {
            p.problem_id for p in user_progress_list if p.status == ProblemProgressStatus.SOLVED
        }
        attempted_unsolved_ids: Set[str] = {
            p.problem_id for p in user_progress_list if p.status == ProblemProgressStatus.ATTEMPTED
        }

        # Mistakes
        mistake_stmt = select(Mistake).where(Mistake.user_id == user.id)
        user_mistakes = (await db.execute(mistake_stmt)).scalars().all()
        mistake_problem_ids: Set[str] = {m.problem_id for m in user_mistakes if m.problem_id}

        # Revision items due
        rev_stmt = select(RevisionItem).where(
            RevisionItem.user_id == user.id,
            RevisionItem.is_active.is_(True),
        )
        due_revisions = (await db.execute(rev_stmt)).scalars().all()
        revision_problem_ids: Set[str] = {
            r.source_id for r in due_revisions if getattr(r.source_type, "value", str(r.source_type)) == "PROBLEM"
        }

        # 4. Filter and score candidates
        candidates: List[ScoredProblemCandidate] = []

        for p in all_problems:
            # If not in revision mode, skip already solved problems
            if mode.upper() != "REVISION" and p.id in solved_ids:
                continue

            score = 10.0
            reasons: List[str] = []
            category = "PRACTICE"

            # Revision Priority (+40)
            if p.id in revision_problem_ids:
                score += 40.0
                reasons.append("Scheduled for spaced repetition revision review.")
                category = "REVISION_DUE"
            elif mode.upper() == "REVISION" and p.id in solved_ids:
                score += 35.0
                reasons.append("Previously solved; selected for spaced retention review.")
                category = "REVISION"

            # Mistake Priority (+35)
            if p.id in mistake_problem_ids:
                score += 35.0
                reasons.append("Prior mistake logged for this problem; recommended to reinforce concept.")
                category = "MISTAKE_PRACTICE"

            # Recently Failed / Attempted (+30)
            if p.id in attempted_unsolved_ids:
                score += 30.0
                reasons.append("Previously attempted but unsolved; ready for a fresh attempt.")
                category = "RECENTLY_FAILED"

            # Pattern Match
            if pattern_id and any(pat.id == pattern_id for pat in p.patterns):
                score += 25.0
                reasons.append("Matches your targeted algorithmic pattern.")
                category = "PATTERN_PRACTICE"

            # Difficulty Fit
            if preferred_difficulty and p.difficulty.value == preferred_difficulty.upper():
                score += 20.0
                reasons.append(f"Calibrated to your preferred difficulty tier ({p.difficulty.value}).")

            # Weak Topic heuristics: if topic has mistakes
            if p.topic_id and any(m.problem and m.problem.topic_id == p.topic_id for m in user_mistakes if m.problem):
                score += 15.0
                reasons.append("Targets an algorithmic topic where cognitive mistakes were recently noted.")
                category = "WEAK_TOPIC"

            if not reasons:
                reasons.append("Selected to build balanced curriculum proficiency.")

            candidates.append(
                ScoredProblemCandidate(
                    problem_id=p.id,
                    slug=p.slug,
                    title=p.title,
                    difficulty=p.difficulty.value,
                    topic_id=p.topic_id,
                    score=score,
                    reasons=reasons,
                    category=category,
                )
            )

        # Sort candidates deterministically: score DESC, problem_id ASC
        candidates.sort(key=lambda c: (-c.score, c.problem_id))
        return candidates[:limit]
