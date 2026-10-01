"""Pydantic schemas for Phase 8 Competitive Programming Arena."""

from pydantic import BaseModel


class CPSampleTestCase(BaseModel):
    """Sample test case displayed in problem statement."""

    input: str
    expected_output: str
    explanation: str | None = None


class CPProblemSummary(BaseModel):
    """Problem listing item inside the Competitive Programming arena."""

    id: str
    problem_id: str
    title: str
    slug: str
    rating_band: int
    difficulty: str
    tags: list[str] = []
    time_limit_ms: int
    memory_limit_mb: int
    solved: bool = False


class CPProblemDetail(BaseModel):
    """Comprehensive problem specification with I/O formats and constraints."""

    id: str
    problem_id: str
    title: str
    slug: str
    description: str
    rating_band: int
    difficulty: str
    tags: list[str] = []
    time_limit_ms: int
    memory_limit_mb: int
    input_format: str
    output_format: str
    constraints: str
    sample_cases: list[CPSampleTestCase] = []
    editorial: str | None = None
    solved: bool = False


class CPRatingProfile(BaseModel):
    """Competitive programming skill rating and stats."""

    user_id: str
    display_name: str
    current_rating: int
    peak_rating: int
    contests_played: int
    contests_won: int
    problems_solved: int
    rank_title: (
        str  # e.g., "Novice", "Pupil", "Specialist", "Expert", "Master", "Grandmaster"
    )


class CPLeaderboardEntry(BaseModel):
    """Competitive rating leaderboard item."""

    rank: int
    display_name: str
    current_rating: int
    peak_rating: int
    contests_played: int
    problems_solved: int
    rank_title: str


class CPLeaderboardResponse(BaseModel):
    """Scoreboard response for competitive programming rating."""

    total: int
    entries: list[CPLeaderboardEntry] = []
