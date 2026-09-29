"""Pydantic request and response schemas for Phase 7 Practice & Gamification."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────
# 1. PRACTICE SESSIONS
# ─────────────────────────────────────────────────────────────

class CreatePracticeSessionRequest(BaseModel):
    """Payload to launch a practice session."""
    mode: str = Field("QUICK", description="Practice mode: QUICK, TOPIC, PATTERN, DIFFICULTY, WEAK_AREA, MISTAKES, REVISION")
    topic_id: Optional[str] = Field(None, description="Optional target topic identifier")
    pattern_id: Optional[str] = Field(None, description="Optional target algorithmic pattern identifier")
    difficulty: Optional[str] = Field(None, description="Optional preferred difficulty tier: EASY, MEDIUM, HARD, EXPERT")
    target_count: int = Field(3, ge=1, le=10, description="Target problem batch size (1 to 10)")


class PracticeSessionProblemResponse(BaseModel):
    """Problem item rendered inside an active practice session."""
    id: str
    problem_id: str
    sequence: int
    title: str
    slug: str
    difficulty: str
    attempted: bool
    solved: bool
    time_spent_seconds: int


class PracticeSessionResponse(BaseModel):
    """Complete practice session state."""
    id: str
    user_id: str
    mode: str
    status: str
    target_count: int
    completed_count: int
    solved_count: int
    xp_earned: int
    accuracy: float
    duration_seconds: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    problems: List[PracticeSessionProblemResponse] = []


class RecordProblemResultRequest(BaseModel):
    """Payload to record the outcome of a practice problem attempt."""
    problem_id: str
    solved: bool
    time_spent_seconds: int = Field(0, ge=0)
    submission_id: Optional[str] = None


class RecordProblemResultResponse(BaseModel):
    """Result of problem attempt recording."""
    session_id: str
    problem_id: str
    solved: bool
    xp_awarded: int
    accuracy: float


# ─────────────────────────────────────────────────────────────
# 2. RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────

class RecommendationItemResponse(BaseModel):
    """Individually scored problem recommendation candidate."""
    problem_id: str
    slug: str
    title: str
    difficulty: str
    score: float
    reasons: List[str]
    category: str


class PracticeRecommendationsResponse(BaseModel):
    """Curated list of practice recommendations."""
    mode: str
    recommendations: List[RecommendationItemResponse]


class ExplainRecommendationResponse(BaseModel):
    """Pedagogical explanation of why a problem was selected."""
    problem_id: str
    title: str
    explanation: str
    pedagogical_factors: List[str]


# ─────────────────────────────────────────────────────────────
# 3. DAILY CHALLENGE
# ─────────────────────────────────────────────────────────────

class DailyChallengeResponse(BaseModel):
    """Authoritative daily challenge state."""
    id: str
    challenge_date: str
    problem_id: str
    problem_title: str
    problem_slug: str
    difficulty: str
    xp_reward: int
    bonus_xp: int
    solved: bool
    first_attempt_solve: bool
    xp_awarded: int
    can_claim: bool


class ClaimDailyRewardResponse(BaseModel):
    """Result of claiming daily challenge reward."""
    success: bool
    xp_awarded: int
    message: str


# ─────────────────────────────────────────────────────────────
# 4. GAMIFICATION PROFILE & XP
# ─────────────────────────────────────────────────────────────

class GamificationProfileResponse(BaseModel):
    """Learner profile overview with level, streak, and rating."""
    total_xp: int
    current_level: int
    level_floor_xp: int
    level_ceiling_xp: int
    xp_in_level: int
    xp_needed_for_next_level: int
    progress_percent: float
    current_streak: int
    longest_streak: int
    current_rating: int
    total_solves: int


class XPTransactionItem(BaseModel):
    """Individual record in the immutable XP ledger."""
    id: str
    event_type: str
    source_id: str
    amount: int
    created_at: datetime


class XPTransactionsResponse(BaseModel):
    """Paginated XP history."""
    total_count: int
    transactions: List[XPTransactionItem]


# ─────────────────────────────────────────────────────────────
# 5. STREAK & ACHIEVEMENTS
# ─────────────────────────────────────────────────────────────

class StreakResponse(BaseModel):
    """Learner streak details."""
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[str] = None
    streak_freeze_count: int
    active_today: bool


class AchievementItem(BaseModel):
    """Badge item with unlock status."""
    id: str
    code: str
    title: str
    description: str
    category: str
    tier: str
    xp_reward: int
    icon: str
    unlocked: bool
    unlocked_at: Optional[datetime] = None


class AchievementsResponse(BaseModel):
    """Learner achievement catalog and progress."""
    total_achievements: int
    unlocked_count: int
    achievements: List[AchievementItem]


# ─────────────────────────────────────────────────────────────
# 6. RATING
# ─────────────────────────────────────────────────────────────

class RatingHistoryItem(BaseModel):
    """Individual skill rating change log."""
    id: str
    previous_rating: int
    new_rating: int
    change: int
    reason: str
    created_at: datetime


class RatingResponse(BaseModel):
    """Learner rating overview and audit log."""
    current_rating: int
    history: List[RatingHistoryItem]
