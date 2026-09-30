"""Pydantic schemas for Phase 8 Interview Mode."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    """Payload to initialize a technical interview simulation."""
    mode: str = Field("GENERAL_SOFTWARE", description="Mode: GENERAL_SOFTWARE, DSA, PYTHON, JAVA, SQL, OOP, MIXED_TECHNICAL")
    duration_minutes: int = Field(45, ge=15, le=90, description="Session duration in minutes")
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    difficulty: Optional[str] = "MEDIUM"


class InterviewQuestionResponse(BaseModel):
    """Interview question presented to student (answers protected)."""
    id: str
    sequence: int
    question_type: str = "CODING"  # MCQ, CODING, SQL, OOP, DEBUGGING, CONCEPTUAL
    question_title: str
    question_prompt: str
    title: Optional[str] = None
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    difficulty: str = "MEDIUM"
    category: Optional[str] = "Technical"
    time_limit_minutes: Optional[int] = 15
    user_answer: Optional[str] = None
    user_response: Optional[str] = None
    code_language: Optional[str] = None
    is_answered: bool = False
    score: Optional[int] = None
    feedback: Optional[str] = None


class InterviewSessionResponse(BaseModel):
    """Interactive interview session state with server-authoritative timer."""
    id: str
    user_id: str
    mode: str
    status: str
    started_at: datetime
    duration_seconds: int
    duration_minutes: Optional[int] = None
    remaining_seconds: int
    is_expired: bool
    total_questions: int
    answered_questions: int
    score: int
    overall_score: Optional[int] = None
    verdict: Optional[str] = None
    evaluation_status: str
    feedback_summary: Optional[str] = None
    rubric_breakdown: Optional[Dict[str, Any]] = None
    improvement_areas: Optional[List[str]] = None
    questions: List[InterviewQuestionResponse] = []


class SubmitInterviewAnswerRequest(BaseModel):
    """Student submission for an interview question."""
    question_id: Optional[str] = None
    answer: Optional[str] = None
    user_response: Optional[str] = None
    code_language: Optional[str] = None


class SubmitInterviewAnswerResponse(BaseModel):
    """Confirmation of answer submission."""
    question_id: str
    answered: bool
    remaining_seconds: int
    is_expired: bool
    message: Optional[str] = "Answer submitted successfully"
    score: Optional[int] = None
    feedback: Optional[str] = None


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
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0
    time_spent_seconds: int = 0
    overall_score: int = 0
    verdict: Optional[str] = "PASSED"
    total_questions: int = 0
    correct_questions: int = 0
    category_scores: List[InterviewCategoryScore] = []
    rubric_breakdown: Optional[Dict[str, Any]] = {}
    time_management_feedback: Optional[str] = ""
    feedback_summary: Optional[str] = ""
    strengths: List[str] = []
    areas_to_improve: List[str] = []
    improvement_areas: Optional[List[str]] = []
    recommended_topics: List[str] = []
    recommended_problems: Optional[List[Dict[str, Any]]] = []
    ai_debrief: Optional[str] = None


class InterviewCoachRequest(BaseModel):
    """Query to the AI Interview Coach during or after an interview."""
    question_id: Optional[str] = None
    message: str = Field(..., min_length=2, max_length=2000)


class InterviewCoachResponse(BaseModel):
    """Educational feedback from AI Interview Coach."""
    reply: str
    suggestion: Optional[str] = None
