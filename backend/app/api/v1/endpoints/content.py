"""Student read-only API endpoints for curricula, tracks, topics, lessons, and problems."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_content_service, get_current_user_optional, get_db
from backend.app.judge.runner import run_sample_test_cases
from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ProblemDifficulty,
)
from backend.app.models.user import User
from backend.app.schemas.judge import RunCodeRequest
from backend.app.services.content_service import ContentService
from backend.app.services.rate_limiter import rate_limiter

router = APIRouter()


# --- Curricula & Tracks ---


@router.get("/curricula", response_model=dict)
async def list_curricula(
    content_service: ContentService = Depends(get_content_service),
):
    """Returns list of all published curricula."""
    curricula = await content_service.get_curricula_list()
    return {"success": True, "data": [c.model_dump() for c in curricula]}


@router.get("/curricula/{slug_or_id}", response_model=dict)
async def get_curriculum(
    slug_or_id: str,
    content_service: ContentService = Depends(get_content_service),
):
    """Returns published curriculum with associated learning tracks."""
    curriculum = await content_service.get_curriculum_by_slug(slug_or_id)
    return {"success": True, "data": curriculum.model_dump()}


# --- Topics & Subtopics ---


@router.get("/topics", response_model=dict)
async def list_topics(
    track_id: str | None = Query(None, description="Filter by learning track UUID"),
    difficulty: ContentLevel | None = Query(
        None, description="Filter by pedagogical difficulty"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size limit"),
    content_service: ContentService = Depends(get_content_service),
):
    """Returns paginated list of published topics."""
    data = await content_service.get_topics_list(
        track_id=track_id,
        difficulty=difficulty,
        page=page,
        page_size=page_size,
    )
    return {"success": True, "data": data.model_dump()}


@router.get("/topics/{slug_or_id}", response_model=dict)
async def get_topic(
    slug_or_id: str,
    content_service: ContentService = Depends(get_content_service),
):
    """Returns topic detail with associated subtopics."""
    topic = await content_service.get_topic_detail(slug_or_id)
    return {"success": True, "data": topic.model_dump()}


@router.get("/subtopics/{subtopic_id}", response_model=dict)
async def get_subtopic(
    subtopic_id: str,
    content_service: ContentService = Depends(get_content_service),
):
    """Returns subtopic summary."""
    subtopic = await content_service.get_subtopic_detail(subtopic_id)
    return {"success": True, "data": subtopic.model_dump()}


# --- Lessons ---


@router.get("/lessons/{slug_or_id}", response_model=dict)
async def get_lesson(
    slug_or_id: str,
    current_user: User | None = Depends(get_current_user_optional),
    content_service: ContentService = Depends(get_content_service),
):
    """Returns lesson with structured blocks. Enforces Premium gate if applicable."""
    lesson = await content_service.get_lesson_detail(
        slug_or_id=slug_or_id,
        current_user=current_user,
    )
    return {"success": True, "data": lesson.model_dump()}


# --- Problems ---


@router.get("/problems", response_model=dict)
async def list_problems(
    topic_slug: str | None = Query(None, description="Filter by parent topic slug"),
    difficulty: ProblemDifficulty | None = Query(
        None, description="Filter by EASY, MEDIUM, HARD, EXPERT"
    ),
    access_level: ContentAccessLevel | None = Query(
        None, description="Filter by FREE or PREMIUM"
    ),
    tag: str | None = Query(
        None, description="Filter by tag slug (e.g. array, hash-table)"
    ),
    pattern: str | None = Query(
        None, description="Filter by pattern slug (e.g. two-pointers, sliding-window)"
    ),
    search: str | None = Query(
        None, min_length=1, max_length=100, description="Safe title search query"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size limit"),
    content_service: ContentService = Depends(get_content_service),
):
    """Returns paginated, searchable problem directory."""
    data = await content_service.get_problems_list(
        topic_slug=topic_slug,
        difficulty=difficulty,
        access_level=access_level,
        tag_slug=tag,
        pattern_slug=pattern,
        search=search,
        page=page,
        page_size=page_size,
    )
    return {"success": True, "data": data.model_dump()}


@router.get("/problems/{slug_or_id}", response_model=dict)
async def get_problem(
    slug_or_id: str,
    current_user: User | None = Depends(get_current_user_optional),
    content_service: ContentService = Depends(get_content_service),
):
    """Fetches problem specification.

    SECURITY INVARIANTS:
    1. Premium Gate: Free users without active entitlement receive 403 Forbidden.
    2. Hidden Test Case Suppression: Hidden test cases are strictly excluded from output.
    """
    problem = await content_service.get_problem_detail(
        slug_or_id=slug_or_id,
        current_user=current_user,
    )
    return {"success": True, "data": problem.model_dump()}


@router.post("/problems/{slug_or_id}/run", response_model=dict)
async def run_problem_code(
    slug_or_id: str,
    payload: RunCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Executes code against sample test cases in an isolated sandbox.

    CRITICAL NON-GOALS & SECURITY INVARIANTS:
    1. NEVER writes to the `submissions` table or alters `UserProblemProgress`.
    2. NEVER evaluates against hidden test cases.
    3. Strictly enforces 64KB source code cap and language allowlist.
    """
    rate_key = f"run:{current_user.id}" if current_user else "run:guest"
    await rate_limiter.check_rate_limit(rate_key, max_requests=60, window_seconds=60)

    result = await run_sample_test_cases(
        db=db,
        problem_id_or_slug=slug_or_id,
        language=payload.language,
        source_code=payload.source_code,
        custom_input=payload.custom_input,
    )
    return {"success": True, "data": result.model_dump()}
