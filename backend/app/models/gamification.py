"""Phase 7: Practice Engine & Gamification domain models.

Provides models for:
- Practice Sessions and Problem Sequence Tracking
- Immutable XP Transaction Ledger
- User Gamification Profile (Level, Streak, Rating, Solves)
- Daily Challenge and User Daily Challenge Completion
- Achievements and User Achievement Unlocks
- Rating History
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base

if TYPE_CHECKING:
    from backend.app.models.content import Problem, ProblemPattern, Topic
    from backend.app.models.progress import Submission
    from backend.app.models.user import User


class PracticeMode(str, enum.Enum):
    """Categorical practice mode selection."""

    QUICK = "QUICK"
    TOPIC = "TOPIC"
    PATTERN = "PATTERN"
    DIFFICULTY = "DIFFICULTY"
    WEAK_AREA = "WEAK_AREA"
    MISTAKES = "MISTAKES"
    REVISION = "REVISION"
    DAILY_CHALLENGE = "DAILY_CHALLENGE"


class PracticeSessionStatus(str, enum.Enum):
    """Lifecycle state of an interactive practice session."""

    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class PracticeSession(Base):
    """Active or historical practice session container."""

    __tablename__ = "practice_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode: Mapped[str] = mapped_column(
        String(32), default=PracticeMode.QUICK.value, nullable=False, index=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pattern_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("patterns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    difficulty: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32),
        default=PracticeSessionStatus.IN_PROGRESS.value,
        nullable=False,
        index=True,
    )
    target_count: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    completed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    xp_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    topic: Mapped[Optional["Topic"]] = relationship("Topic", foreign_keys=[topic_id])
    pattern: Mapped[Optional["ProblemPattern"]] = relationship(
        "ProblemPattern", foreign_keys=[pattern_id]
    )
    session_problems: Mapped[list["PracticeSessionProblem"]] = relationship(
        "PracticeSessionProblem",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="PracticeSessionProblem.sequence",
    )

    __table_args__ = (
        Index("ix_practice_sessions_user_status", "user_id", "status"),
        Index("ix_practice_sessions_user_created", "user_id", "created_at"),
    )


class PracticeSessionProblem(Base):
    """Problems served within a specific practice session."""

    __tablename__ = "practice_session_problems"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    served_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    attempted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    solved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submission_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True
    )
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    session: Mapped["PracticeSession"] = relationship(
        "PracticeSession", back_populates="session_problems"
    )
    problem: Mapped["Problem"] = relationship("Problem", foreign_keys=[problem_id])
    submission: Mapped[Optional["Submission"]] = relationship(
        "Submission", foreign_keys=[submission_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id", "problem_id", name="uq_practice_session_problem"
        ),
        Index("ix_session_problem_session_seq", "session_id", "sequence"),
    )


class XPTransaction(Base):
    """Immutable ledger of all XP grants, rewards, and milestone events."""

    __tablename__ = "xp_transactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(160), unique=True, nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_xp_trans_user_created", "user_id", "created_at"),
        Index("ix_xp_trans_user_event", "user_id", "event_type"),
    )


class UserGamificationProfile(Base):
    """Authoritative gamification state for a user (Level, XP, Streak, Rating, Solves)."""

    __tablename__ = "user_gamification_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    total_xp: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True
    )
    current_level: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, index=True
    )
    current_streak: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True
    )
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_activity_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # YYYY-MM-DD
    streak_freeze_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_rating: Mapped[int] = mapped_column(
        Integer, default=1000, nullable=False, index=True
    )
    total_solves: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_gamification_xp_rank", "total_xp"),
        Index("ix_gamification_solves_rank", "total_solves"),
        Index("ix_gamification_streak_rank", "current_streak"),
    )


class DailyChallenge(Base):
    """Daily challenge definition per calendar date."""

    __tablename__ = "daily_challenges"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    challenge_date: Mapped[str] = mapped_column(
        String(10), unique=True, nullable=False, index=True
    )  # YYYY-MM-DD
    problem_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    bonus_xp: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    problem: Mapped["Problem"] = relationship("Problem", foreign_keys=[problem_id])
    user_challenges: Mapped[list["UserDailyChallenge"]] = relationship(
        "UserDailyChallenge",
        back_populates="daily_challenge",
        cascade="all, delete-orphan",
    )


class UserDailyChallenge(Base):
    """User participation and completion record for a daily challenge."""

    __tablename__ = "user_daily_challenges"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    daily_challenge_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("daily_challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    challenge_date: Mapped[str] = mapped_column(
        String(10), nullable=False, index=True
    )  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(32), default="ATTEMPTED", nullable=False)
    attempts_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_attempt_solve: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    daily_challenge: Mapped["DailyChallenge"] = relationship(
        "DailyChallenge", back_populates="user_challenges"
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id", "challenge_date", name="uq_user_daily_challenge_date"
        ),
        Index("ix_user_daily_challenges_user_solved", "user_id", "solved"),
    )


class Achievement(Base):
    """Master catalog of badges and milestones achievable by learners."""

    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    code: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(16), default="BRONZE", nullable=False)
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    icon: Mapped[str] = mapped_column(String(64), default="trophy", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )


class UserAchievement(Base):
    """Record of an unlocked achievement for a specific learner."""

    __tablename__ = "user_achievements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    achievement: Mapped["Achievement"] = relationship(
        "Achievement", back_populates="user_achievements"
    )

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
        Index("ix_user_achievements_user_unlocked", "user_id", "unlocked_at"),
    )


class RatingHistory(Base):
    """Historical audit trail of practice rating changes."""

    __tablename__ = "rating_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    new_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(128), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    __table_args__ = (Index("ix_rating_history_user_created", "user_id", "created_at"),)
