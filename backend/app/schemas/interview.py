"""Pydantic schemas for Phase 8 Interview Mode."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    """Payload to initialize a technical interview simulation."""

    mode: str = Field(
        "GENERAL_SOFTWARE",
        description="Mode: GENERAL_SOFTWARE, DSA, PYTHON, JAVA, SQL, OOP, MIXED_TECHNICAL",
    )
    duration_minutes: int = Field(
        45, ge=15, le=90, description="Session duration in minutes"
    )
    target_company: str | None = None
    target_role: str | None = None
    difficulty: str | None = "MEDIUM"


class InterviewQuestionResponse(BaseModel):
    """Interview question presented to student (answers protected)."""

    id: str
    sequence: int
    question_type: str = "CODING"  # MCQ, CODING, SQL, OOP, DEBUGGING, CONCEPTUAL
    question_title: str
    question_prompt: str
    title: str | None = None
    question_text: str | None = None
    options: list[str] | None = None
    difficulty: str = "MEDIUM"
    category: str | None = "Technical"
    time_limit_minutes: int | None = 15
    user_answer: str | None = None
    user_response: str | None = None
    code_language: str | None = None
    is_answered: bool = False
    score: int | None = None
    feedback: str | None = None


class InterviewSessionResponse(BaseModel):
    """Interactive interview session state with server-authoritative timer."""

    id: str
    user_id: str
    mode: str
    status: str
    started_at: datetime
    duration_seconds: int
    duration_minutes: int | None = None
    remaining_seconds: int
    is_expired: bool
    total_questions: int
    answered_questions: int
    score: int
    overall_score: int | None = None
    verdict: str | None = None
    evaluation_status: str
    feedback_summary: str | None = None
    rubric_breakdown: dict[str, Any] | None = None
    improvement_areas: list[str] | None = None
    questions: list[InterviewQuestionResponse] = []


class SubmitInterviewAnswerRequest(BaseModel):
    """Student submission for an interview question."""

    question_id: str | None = None
    answer: str | None = None
    user_response: str | None = None
    code_language: str | None = None


class SubmitInterviewAnswerResponse(BaseModel):
    """Confirmation of answer submission."""

    question_id: str
    answered: bool
    remaining_seconds: int
    is_expired: bool
    message: str | None = "Answer submitted successfully"
    score: int | None = None
    feedback: str | None = None


class InterviewCategoryScore(BaseModel):
    """Performance breakdown for a technical category."""

    category: str
    score: int
    total_possible: int
    percentage: float


class InterviewReportResponse(BaseModel):
    """Comprehensive performance scorecard generated at interview completion."""

    session_id: str
    mode: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: int = 0
    time_spent_seconds: int = 0
    overall_score: int = 0
    verdict: str | None = "PASSED"
    total_questions: int = 0
    correct_questions: int = 0
    category_scores: list[InterviewCategoryScore] = []
    rubric_breakdown: dict[str, Any] | None = {}
    time_management_feedback: str | None = ""
    feedback_summary: str | None = ""
    strengths: list[str] = []
    areas_to_improve: list[str] = []
    improvement_areas: list[str] | None = []
    recommended_topics: list[str] = []
    recommended_problems: list[dict[str, Any]] | None = []
    ai_debrief: str | None = None


class InterviewCoachRequest(BaseModel):
    """Query to the AI Interview Coach during or after an interview."""

    question_id: str | None = None
    message: str = Field(..., min_length=2, max_length=2000)


class InterviewCoachResponse(BaseModel):
    """Educational feedback from AI Interview Coach."""

    reply: str
    suggestion: str | None = None
