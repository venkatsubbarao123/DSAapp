"""SQL Learning and Practice Engine API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import (
    get_current_user,
    get_current_user_optional,
    get_db,
)
from backend.app.models.user import User
from backend.app.schemas.sql_learning import (
    RunSQLQueryRequest,
    RunSQLQueryResponse,
    SQLProblemDetail,
    SQLProblemSummary,
    SQLSubmissionSummary,
    SubmitSQLQueryRequest,
    SubmitSQLQueryResponse,
)
from backend.app.services.sql.sql_service import SQLService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/problems", response_model=list[SQLProblemSummary])
async def list_sql_problems(
    category: str | None = Query(
        None,
        description="Filter by category (BASICS, JOINS, AGGREGATIONS, WINDOW_FUNCTIONS)",
    ),
    difficulty: str | None = Query(
        None, description="Filter by difficulty: EASY, MEDIUM, HARD"
    ),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Lists SQL practice problems with difficulty and user solved status."""
    user_id = current_user.id if current_user else None
    return await SQLService.list_problems(db, user_id, category, difficulty)


@router.get("/problems/{slug}", response_model=SQLProblemDetail)
async def get_sql_problem(
    slug: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves full SQL problem specification with test schema and sample data."""
    user_id = current_user.id if current_user else None
    problem = await SQLService.get_problem_by_slug_or_id(db, slug, user_id)
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SQL problem not found.",
        )
    return problem


@router.post("/problems/{slug}/run", response_model=RunSQLQueryResponse)
async def dry_run_sql_query(
    slug: str,
    payload: RunSQLQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Executes SQL query in dry-run mode against isolated sandbox schema."""
    return await SQLService.dry_run_query(db, slug, payload.query)


@router.post("/problems/{slug}/submit", response_model=SubmitSQLQueryResponse)
async def submit_sql_query(
    slug: str,
    payload: SubmitSQLQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submits student SQL query for authoritative grading inside isolated sandbox."""
    return await SQLService.submit_query(db, current_user.id, slug, payload.query)


@router.get("/problems/{slug}/submissions", response_model=list[SQLSubmissionSummary])
async def list_my_sql_submissions(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Lists current authenticated user's past SQL submission attempts."""
    return await SQLService.list_user_submissions(db, current_user.id, slug)
