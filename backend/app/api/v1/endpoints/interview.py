"""Technical Interview Simulation API endpoints."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.interview import InterviewSession
from backend.app.models.user import User
from backend.app.schemas.interview import (
    InterviewCoachRequest,
    InterviewCoachResponse,
    InterviewReportResponse,
    InterviewSessionResponse,
    StartInterviewRequest,
    SubmitInterviewAnswerRequest,
    SubmitInterviewAnswerResponse,
)
from backend.app.services.interview.interview_service import InterviewService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/sessions", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_interview_session(
    payload: StartInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Starts a new technical interview simulation across selected technical mode."""
    return await InterviewService.create_session(db, current_user, payload)


@router.get("/sessions", response_model=List[dict])
async def list_my_interviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists current authenticated user's past and in-progress interview sessions."""
    stmt = (
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.started_at.desc())
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    return [
        {
            "id": s.id,
            "mode": s.mode,
            "status": s.status,
            "started_at": s.started_at,
            "completed_at": s.completed_at,
            "duration_seconds": s.duration_seconds,
            "remaining_seconds": s.remaining_seconds,
            "total_questions": s.total_questions,
            "answered_questions": s.answered_questions,
            "score": s.score,
            "evaluation_status": s.evaluation_status,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
async def get_interview_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves session state with server-authoritative countdown (IDOR protected)."""
    session = await InterviewService.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview session not found or access denied.",
        )
    return session


@router.post("/sessions/{session_id}/answer", response_model=SubmitInterviewAnswerResponse)
async def submit_question_answer(
    session_id: str,
    payload: SubmitInterviewAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submits student answer for an interview question with server-side validation."""
    resp, err = await InterviewService.submit_answer(db, session_id, current_user.id, payload)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err,
        )
    return resp


@router.post("/sessions/{session_id}/finish", response_model=InterviewReportResponse)
async def finish_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually completes interview and returns evaluated performance scorecard."""
    report, err = await InterviewService.finish_session(db, session_id, current_user.id)
    if err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err,
        )
    return report


@router.get("/sessions/{session_id}/report", response_model=InterviewReportResponse)
async def get_interview_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves comprehensive interview performance report with category breakdown."""
    report = await InterviewService.get_report(db, session_id, current_user.id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview report not found or access denied.",
        )
    return report


@router.post("/sessions/{session_id}/coach", response_model=InterviewCoachResponse)
async def ask_interview_coach(
    session_id: str,
    payload: InterviewCoachRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Consults the AI Interview Coach for educational hints and conceptual guidance."""
    return await InterviewService.ask_coach(db, session_id, current_user.id, payload)
