"""Pydantic schemas for Phase 6 AI Learning System."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ─────────────────────────────────────────────────────────────────────────────
# 1. AI Tutor Schemas
# ─────────────────────────────────────────────────────────────────────────────


class TutorRequest(BaseModel):
    """Input payload for student question to AI Tutor."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ...,
        min_length=2,
        max_length=2000,
        description="The learner's question or topic of inquiry.",
    )
    problem_id: str | None = Field(
        None, max_length=128, description="Optional problem context ID or slug."
    )
    lesson_id: str | None = Field(
        None, max_length=36, description="Optional lesson context ID."
    )
    conversation_id: str | None = Field(
        None, max_length=36, description="Optional conversation session ID."
    )
    code_context: str | None = Field(
        None, max_length=10000, description="Optional source code snippet for context."
    )


class VisualizationSuggestion(BaseModel):
    """Optional reference suggesting an interactive visualizer for the concept."""

    visualizer_type: str = Field(
        ..., description="Visualizer identifier e.g. binary-search, two-pointers, bst"
    )
    title: str = Field(..., description="Display title for the visualizer.")
    description: str = Field(
        ..., description="Short explanation of what to observe in the visualizer."
    )
    initial_data: dict[str, Any] | None = Field(
        None, description="Pre-configured algorithm parameters."
    )


class TutorResponse(BaseModel):
    """Pedagogically structured response from AI Tutor."""

    explanation: str = Field(..., description="Clear, pedagogical concept explanation.")
    key_idea: str = Field(..., description="Core intuition or mental model.")
    example: str | None = Field(None, description="Concrete illustrative walkthrough.")
    next_step: str | None = Field(
        None, description="Guiding question or suggestion for learner to try next."
    )
    related_concept: str | None = Field(
        None, description="Related DSA concept or pattern to connect knowledge."
    )
    visualization_suggestion: VisualizationSuggestion | None = Field(
        None, description="Suggested interactive visualizer."
    )
    conversation_id: str | None = Field(
        None, description="Conversation session ID for continuity."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 2. Progressive Hint Schemas
# ─────────────────────────────────────────────────────────────────────────────


class HintRequest(BaseModel):
    """Request for progressive tier of problem hints."""

    model_config = ConfigDict(extra="forbid")

    problem_id: str = Field(
        ..., min_length=1, max_length=128, description="ID or slug of the problem."
    )
    hint_level: int = Field(
        ..., ge=1, le=5, description="Requested hint tier (1 to 5)."
    )
    current_code: str | None = Field(
        None, max_length=10000, description="Optional current learner draft code."
    )


class HintResponse(BaseModel):
    """Tiered progressive hint disclosure."""

    problem_id: str
    problem_title: str
    hint_level: int = Field(..., ge=1, le=5)
    max_level: int = Field(5, description="Maximum available hint tiers.")
    title: str = Field(..., description="Tier summary title.")
    hint_content: str = Field(
        ...,
        description="Guiding hint text without giving away raw copy-paste solution.",
    )
    thought_question: str = Field(
        ..., description="Reflective prompt to stimulate learner reasoning."
    )
    is_last_hint: bool = Field(False)


# ─────────────────────────────────────────────────────────────────────────────
# 3. AI Explanation Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ExplainRequest(BaseModel):
    """Request for detailed conceptual or diagnostic explanation."""

    model_config = ConfigDict(extra="forbid")

    target_type: Literal[
        "concept", "algorithm", "code", "judge_error", "complexity", "pattern"
    ] = Field(..., description="The type of entity to explain.")
    context_text: str = Field(
        ...,
        min_length=2,
        max_length=12000,
        description="Code, error message, or concept query.",
    )
    problem_id: str | None = Field(None, max_length=128)
    submission_id: str | None = Field(None, max_length=128)
    language: str | None = Field(None, max_length=32)


class ExplainResponse(BaseModel):
    """Detailed educational explanation."""

    target_type: str
    explanation: str = Field(..., description="Comprehensive explanation.")
    breakdown_points: list[str] = Field(
        default_factory=list, description="Step-by-step diagnostic breakdown."
    )
    key_takeaways: list[str] = Field(
        default_factory=list, description="Core takeaways."
    )
    code_review_points: list[str] | None = Field(
        None, description="Constructive feedback points if code was analyzed."
    )
    suggested_fix: str | None = Field(
        None, description="Conceptual direction for remediation (no raw answer dump)."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Complexity Analyzer Schemas
# ─────────────────────────────────────────────────────────────────────────────


class ComplexityRequest(BaseModel):
    """Input payload for Big-O analysis."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        min_length=5,
        max_length=15000,
        description="Student code or pseudocode to analyze.",
    )
    language: str | None = Field("python", max_length=32)
    problem_id: str | None = Field(None, max_length=128)


class ComplexityResponse(BaseModel):
    """Structured Big-O time and space complexity evaluation."""

    time_complexity: str = Field(..., description="e.g. O(n), O(n log n), O(n^2)")
    space_complexity: str = Field(..., description="e.g. O(1), O(n)")
    best_case: str = Field(..., description="Best-case time bound with condition.")
    average_case: str = Field(..., description="Average-case time bound.")
    worst_case: str = Field(..., description="Worst-case time bound.")
    reasoning: str = Field(
        ...,
        description="Mathematical derivation and step-by-step loop/recursion analysis.",
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Confidence level of analysis."
    )
    caveats: list[str] = Field(
        default_factory=list,
        description="Assumptions, auxiliary space caveats, language runtime specifics.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. DSA Pattern Detector Schemas
# ─────────────────────────────────────────────────────────────────────────────


class PatternRequest(BaseModel):
    """Input payload for algorithmic pattern recognition."""

    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(
        None,
        max_length=15000,
        description="Optional implementation to detect pattern in.",
    )
    problem_description: str | None = Field(
        None,
        max_length=5000,
        description="Optional problem text to detect patterns for.",
    )
    problem_id: str | None = Field(None, max_length=128)


class PatternEvidence(BaseModel):
    """Evidence line supporting pattern detection."""

    indicator: str = Field(
        ...,
        description="Specific clue (e.g. 'sorted array search', 'subarray window bounds', 'LIFO state').",
    )
    relevance: str = Field(..., description="Why this clue indicates the pattern.")


class PatternResponse(BaseModel):
    """Algorithmic pattern detection outcome."""

    primary_pattern: str = Field(
        ...,
        description="Leading identified DSA pattern (e.g. 'Two Pointers', 'Sliding Window').",
    )
    confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(...)
    detected_patterns: list[str] = Field(
        default_factory=list, description="All matching pattern candidates."
    )
    evidence: list[PatternEvidence] = Field(
        default_factory=list,
        description="Concrete indicators supporting the detection.",
    )
    alternative_patterns: list[str] = Field(
        default_factory=list, description="Feasible trade-off or alternative patterns."
    )
    explanation: str = Field(
        ..., description="Educational explanation of why this pattern is optimal."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Personalized Recommendations Schemas
# ─────────────────────────────────────────────────────────────────────────────


class RecommendationItem(BaseModel):
    """Individual targeted learning recommendation."""

    topic_id: str
    topic_title: str
    problem_id: str
    problem_title: str
    difficulty: str
    reason: str = Field(
        ..., description="Personalized pedagogical reason based on progress / mistakes."
    )
    priority: Literal["HIGH", "MEDIUM", "LOW"] = Field(...)
    estimated_effort_minutes: int = Field(..., ge=5, le=120)
    related_pattern: str | None = None


class WeakTopicItem(BaseModel):
    """Identified weak topic derived from mistake frequency."""

    topic_id: str
    topic_title: str
    mistake_count: int
    unsolved_attempts: int
    suggested_action: str


class RecommendationResponse(BaseModel):
    """Personalized learning recommendations based on actual Phase 4 progress data."""

    has_sufficient_data: bool = Field(
        ..., description="False if learner is brand-new with insufficient history."
    )
    summary_insight: str = Field(
        ..., description="Narrative summary of learner progress and focus areas."
    )
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    weak_topics: list[WeakTopicItem] = Field(default_factory=list)
    pending_revisions_count: int = Field(
        0, description="Number of items currently due in spaced revision queue."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7. AI Usage and Diagnostics Schemas
# ─────────────────────────────────────────────────────────────────────────────


class AIUsageSummaryResponse(BaseModel):
    """Current usage telemetry and quota status."""

    daily_quota: int
    daily_used: int
    daily_remaining: int
    is_premium: bool
    provider: str
    model: str
    can_request: bool
