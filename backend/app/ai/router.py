"""API Router for Phase 6 AI Learning System and Tutor Endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.providers import get_ai_provider
from backend.app.ai.service import AIService
from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.ai import (
    AIUsageSummaryResponse,
    ComplexityRequest,
    ComplexityResponse,
    ExplainRequest,
    ExplainResponse,
    HintRequest,
    HintResponse,
    PatternRequest,
    PatternResponse,
    RecommendationResponse,
    TutorRequest,
    TutorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tutor", response_model=TutorResponse, status_code=status.HTTP_200_OK)
async def ask_tutor(
    request: TutorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TutorResponse:
    """Interacts with the AI DSA Tutor for conceptual explanations and guidance."""
    return await AIService.ask_tutor(db, current_user, request)


@router.post("/hint", response_model=HintResponse, status_code=status.HTTP_200_OK)
async def get_progressive_hint(
    request: HintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HintResponse:
    """Requests progressive hints (Level 1-5) for a specific challenge."""
    return await AIService.get_progressive_hint(db, current_user, request)


@router.post("/explain", response_model=ExplainResponse, status_code=status.HTTP_200_OK)
async def explain_concept_or_code(
    request: ExplainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExplainResponse:
    """Explains algorithmic concepts, code mechanics, or judge execution errors."""
    return await AIService.explain_content(db, current_user, request)


@router.post(
    "/complexity", response_model=ComplexityResponse, status_code=status.HTTP_200_OK
)
async def analyze_complexity(
    request: ComplexityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ComplexityResponse:
    """Analyzes Big-O time and space complexity with best/average/worst breakdown."""
    return await AIService.analyze_complexity(db, current_user, request)


@router.post("/pattern", response_model=PatternResponse, status_code=status.HTTP_200_OK)
async def detect_pattern(
    request: PatternRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PatternResponse:
    """Detects canonical DSA patterns and supplies concrete evidence."""
    return await AIService.detect_pattern(db, current_user, request)


@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_personalized_recommendations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecommendationResponse:
    """Synthesizes recommendations using actual progress, mistakes, and revision data."""
    return await AIService.get_personalized_recommendations(db, current_user)


@router.get(
    "/usage", response_model=AIUsageSummaryResponse, status_code=status.HTTP_200_OK
)
async def get_ai_usage_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIUsageSummaryResponse:
    """Returns the current user's daily quota, usage telemetry, and provider info."""
    return await AIService.get_usage_summary(db, current_user)


@router.get(
    "/diagnostics", response_model=dict[str, Any], status_code=status.HTTP_200_OK
)
async def get_ai_diagnostics(
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """Provides safe diagnostic status of the active AI provider without leaking secrets."""
    provider = get_ai_provider()
    return provider.get_diagnostics()
