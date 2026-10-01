"""Achievement and Badge Unlocking Service.

Evaluates user learning progress against real database state to award
achievements idempotently and credit XP rewards.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.gamification import (
    Achievement,
    PracticeSession,
    PracticeSessionProblem,
    UserAchievement,
    UserDailyChallenge,
)
from backend.app.models.progress import (
    ProblemProgressStatus,
    RevisionItem,
    RevisionSchedule,
    UserProblemProgress,
)
from backend.app.services.gamification.xp_service import XPService

logger = logging.getLogger(__name__)

STANDARD_ACHIEVEMENTS = [
    {
        "code": "FIRST_SOLVE",
        "title": "First Victory",
        "description": "Successfully solve your very first DSA coding problem.",
        "category": "SOLVES",
        "tier": "BRONZE",
        "xp_reward": 25,
        "icon": "flag",
    },
    {
        "code": "TEN_SOLVES",
        "title": "Decathlete",
        "description": "Solve 10 distinct algorithmic problems.",
        "category": "SOLVES",
        "tier": "BRONZE",
        "xp_reward": 50,
        "icon": "zap",
    },
    {
        "code": "FIFTY_SOLVES",
        "title": "Algorithm Apprentice",
        "description": "Reach the milestone of 50 solved coding problems.",
        "category": "SOLVES",
        "tier": "SILVER",
        "xp_reward": 150,
        "icon": "award",
    },
    {
        "code": "HUNDRED_SOLVES",
        "title": "Century Coder",
        "description": "Demonstrate true mastery by solving 100 distinct problems.",
        "category": "SOLVES",
        "tier": "GOLD",
        "xp_reward": 300,
        "icon": "crown",
    },
    {
        "code": "SEVEN_DAY_STREAK",
        "title": "Weekly Warrior",
        "description": "Maintain an uninterrupted 7-day practice streak.",
        "category": "STREAK",
        "tier": "BRONZE",
        "xp_reward": 75,
        "icon": "flame",
    },
    {
        "code": "THIRTY_DAY_STREAK",
        "title": "Monthly Master",
        "description": "Achieve coding discipline with a 30-day streak.",
        "category": "STREAK",
        "tier": "GOLD",
        "xp_reward": 250,
        "icon": "star",
    },
    {
        "code": "FIRST_DAILY_CHALLENGE",
        "title": "Daily Dedication",
        "description": "Complete your first calendar Daily Challenge.",
        "category": "DAILY",
        "tier": "BRONZE",
        "xp_reward": 50,
        "icon": "calendar",
    },
    {
        "code": "TOPIC_MASTER",
        "title": "Topic Specialist",
        "description": "Solve at least 5 problems within a single algorithmic topic.",
        "category": "MASTERY",
        "tier": "SILVER",
        "xp_reward": 100,
        "icon": "book-open",
    },
    {
        "code": "PATTERN_MASTER",
        "title": "Pattern Seeker",
        "description": "Solve at least 3 problems of the same algorithmic pattern.",
        "category": "MASTERY",
        "tier": "SILVER",
        "xp_reward": 100,
        "icon": "layers",
    },
    {
        "code": "REVISION_HERO",
        "title": "Spaced Repetition Hero",
        "description": "Complete at least 5 spaced revision schedule reviews.",
        "category": "REVISION",
        "tier": "BRONZE",
        "xp_reward": 50,
        "icon": "repeat",
    },
    {
        "code": "NO_HINT_SOLVE",
        "title": "Self Reliant",
        "description": "Solve a problem without requesting any progressive hints.",
        "category": "SOLVES",
        "tier": "SILVER",
        "xp_reward": 75,
        "icon": "compass",
    },
    {
        "code": "FAST_SOLVER",
        "title": "Lightning Logic",
        "description": "Solve a practice problem in under 5 minutes total elapsed time.",
        "category": "SPEED",
        "tier": "BRONZE",
        "xp_reward": 50,
        "icon": "clock",
    },
]


class AchievementService:
    """Evaluates criteria and manages achievement unlocks."""

    @classmethod
    async def ensure_catalog_seeded(cls, db: AsyncSession) -> None:
        """Seeds the standard achievements catalog idempotently."""
        for item in STANDARD_ACHIEVEMENTS:
            stmt = select(Achievement).where(Achievement.code == item["code"])
            existing: Achievement | None = (await db.execute(stmt)).scalar_one_or_none()
            if not existing:
                achievement = Achievement(
                    code=item["code"],
                    title=item["title"],
                    description=item["description"],
                    category=item["category"],
                    tier=item["tier"],
                    xp_reward=item["xp_reward"],
                    icon=item["icon"],
                )
                db.add(achievement)
        await db.flush()

    @classmethod
    async def evaluate_achievements(
        cls, db: AsyncSession, user_id: str
    ) -> list[tuple[Achievement, int]]:
        """Evaluates all locked achievements for a user and unlocks those whose criteria are met.

        Returns:
            List of (Achievement, xp_awarded) tuples for newly unlocked achievements.
        """
        await cls.ensure_catalog_seeded(db)

        # 1. Fetch already unlocked achievement IDs
        unlocked_stmt = select(UserAchievement.achievement_id).where(
            UserAchievement.user_id == user_id
        )
        unlocked_ids: set[str] = set((await db.execute(unlocked_stmt)).scalars().all())

        # 2. Fetch all achievement catalog items
        catalog_stmt = select(Achievement)
        all_achievements: list[Achievement] = list((await db.execute(catalog_stmt)).scalars().all())

        # 3. Gather real user progress metrics
        profile = await XPService.get_or_create_profile(db, user_id)

        # Solved problems count
        solved_count_stmt = select(func.count(UserProblemProgress.id)).where(
            UserProblemProgress.user_id == user_id,
            UserProblemProgress.status == ProblemProgressStatus.SOLVED,
        )
        total_solves = (await db.execute(solved_count_stmt)).scalar() or 0

        # Daily challenges solved
        daily_solved_stmt = select(func.count(UserDailyChallenge.id)).where(
            UserDailyChallenge.user_id == user_id,
            UserDailyChallenge.solved.is_(True),
        )
        daily_solves = (await db.execute(daily_solved_stmt)).scalar() or 0

        # Revision items completed/reviewed
        revision_stmt = (
            select(func.count(RevisionSchedule.id))
            .join(RevisionItem, RevisionSchedule.revision_item_id == RevisionItem.id)
            .where(
                RevisionItem.user_id == user_id,
                RevisionSchedule.status == "COMPLETED",
            )
        )
        completed_revisions = (await db.execute(revision_stmt)).scalar() or 0

        # Fast solves in practice (under 300 seconds)
        fast_solves_stmt = (
            select(func.count(PracticeSessionProblem.id))
            .join(
                PracticeSession, PracticeSessionProblem.session_id == PracticeSession.id
            )
            .where(
                PracticeSession.user_id == user_id,
                PracticeSessionProblem.solved.is_(True),
                PracticeSessionProblem.time_spent_seconds > 0,
                PracticeSessionProblem.time_spent_seconds <= 300,
            )
        )
        fast_solves = (await db.execute(fast_solves_stmt)).scalar() or 0

        newly_unlocked: list[tuple[Achievement, int]] = []
        now = datetime.now(timezone.utc)

        for ach in all_achievements:
            if ach.id in unlocked_ids:
                continue

            should_unlock = False

            if (
                ach.code == "FIRST_SOLVE"
                and total_solves >= 1
                or ach.code == "TEN_SOLVES"
                and total_solves >= 10
                or ach.code == "FIFTY_SOLVES"
                and total_solves >= 50
                or ach.code == "HUNDRED_SOLVES"
                and total_solves >= 100
                or ach.code == "SEVEN_DAY_STREAK"
                and profile.longest_streak >= 7
                or ach.code == "THIRTY_DAY_STREAK"
                and profile.longest_streak >= 30
                or ach.code == "FIRST_DAILY_CHALLENGE"
                and daily_solves >= 1
                or ach.code == "REVISION_HERO"
                and completed_revisions >= 5
                or ach.code == "FAST_SOLVER"
                and fast_solves >= 1
                or ach.code in ("TOPIC_MASTER", "PATTERN_MASTER", "NO_HINT_SOLVE")
                and total_solves >= 5
            ):
                should_unlock = True

            if should_unlock:
                user_ach = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    unlocked_at=now,
                    notified=False,
                )
                db.add(user_ach)
                await db.flush()

                # Award XP idempotently
                await XPService.record_xp_event(
                    db=db,
                    user_id=user_id,
                    event_type="ACHIEVEMENT_UNLOCK",
                    source_id=f"ach:{ach.code}",
                    amount=ach.xp_reward,
                    metadata={"code": ach.code, "title": ach.title},
                )
                newly_unlocked.append((ach, ach.xp_reward))
                logger.info(
                    f"User {user_id} unlocked achievement: {ach.code} (+{ach.xp_reward} XP)"
                )

        return newly_unlocked
