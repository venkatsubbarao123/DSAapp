"""Pydantic schemas for Phase 8 Contest System."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ContestSummaryResponse(BaseModel):
    """Contest summary overview for cards and catalogs."""
    id: str
    title: str
    slug: str
    description: str
    status: str
    start_at: datetime
    end_at: datetime
    duration_seconds: int
    remaining_seconds: int
    visibility: str
    premium_required: bool
    participant_count: int = 0


class ContestProblemResponse(BaseModel):
    """Problem specification in a contest."""
    id: str
    problem_id: str
    title: str
    slug: str
    sequence: int
    points: int
    penalty_minutes: int
    difficulty: str
    solved: bool = False
    wrong_attempts: int = 0


class ContestDetailResponse(BaseModel):
    """Full contest details with registered participant state."""
    id: str
    title: str
    slug: str
    description: str
    status: str
    start_at: datetime
    end_at: datetime
    duration_seconds: int
    remaining_seconds: int
    visibility: str
    premium_required: bool
    is_registered: bool = False
    participant_count: int = 0
    my_score: int = 0
    my_penalty: int = 0
    my_rank: Optional[int] = None
    problems: List[ContestProblemResponse] = []


class ContestSubmitRequest(BaseModel):
    """Student solution submission inside an active contest."""
    problem_id: str
    language: str = Field(..., max_length=32)
    source_code: str = Field(..., max_length=65536)
    idempotency_key: Optional[str] = None


class ContestSubmitResponse(BaseModel):
    """Result of enqueuing a contest submission."""
    submission_id: str
    contest_submission_id: str
    verdict: str
    score: int
    penalty: int
    message: str


class ProblemResultDetail(BaseModel):
    """Breakdown of participant's status on a single contest problem."""
    solved: bool
    wrong_attempts: int
    time_minutes: Optional[int] = None
    points: int = 0


class ContestLeaderboardEntry(BaseModel):
    """Single participant ranking row in a contest scoreboard."""
    rank: int
    display_name: str
    score: int
    penalty: int
    problems_solved: int
    problem_results: Dict[str, ProblemResultDetail] = {}


class ContestLeaderboardResponse(BaseModel):
    """Contest scoreboard payload."""
    contest_id: str
    contest_title: str
    status: str
    total_participants: int
    entries: List[ContestLeaderboardEntry] = []


class UserContestHistoryEntry(BaseModel):
    """Contest historical record for user profile."""
    contest_id: str
    contest_title: str
    contest_slug: str
    start_at: datetime
    end_at: datetime
    joined_at: datetime
    final_score: int
    final_penalty: int
    final_rank: Optional[int] = None
    total_participants: int = 0
