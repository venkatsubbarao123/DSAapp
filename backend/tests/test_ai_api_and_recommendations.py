"""Tests for Phase 6 AI endpoints, authorization, quotas, and personalized recommendations."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.models.ai import AIHintUsage
from backend.app.models.content import Problem
from backend.app.models.progress import Mistake, MistakeType, ProblemProgressStatus, Submission, SubmissionStatus, UserProblemProgress
from backend.app.models.user import User


@pytest.fixture(autouse=True)
async def seed_data():
    async with async_session_factory() as session:
        await seed_development_content(session)


async def get_user_token(client: AsyncClient, email: str) -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    return login_res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_ai_endpoints_reject_unauthenticated(client: AsyncClient):
    """All AI endpoints must require authentication."""
    res1 = await client.post("/api/v1/ai/tutor", json={"question": "What is binary search?"})
    assert res1.status_code in (401, 403)

    res2 = await client.post("/api/v1/ai/hint", json={"problem_id": "two-sum-seed", "hint_level": 1})
    assert res2.status_code in (401, 403)

    res3 = await client.post("/api/v1/ai/explain", json={"target_type": "concept", "context_text": "Graph BFS"})
    assert res3.status_code in (401, 403)

    res4 = await client.post("/api/v1/ai/complexity", json={"code": "for i in range(n): pass"})
    assert res4.status_code in (401, 403)

    res5 = await client.post("/api/v1/ai/pattern", json={"problem_description": "Search in sorted array"})
    assert res5.status_code in (401, 403)

    res6 = await client.get("/api/v1/ai/recommendations")
    assert res6.status_code in (401, 403)

    res7 = await client.get("/api/v1/ai/usage")
    assert res7.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ai_tutor_endpoint(client: AsyncClient):
    token = await get_user_token(client, "student_tutor@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/ai/tutor",
        json={"question": "How do two pointers work for finding pairs that sum to target?"},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "explanation" in data
    assert "key_idea" in data
    assert data["conversation_id"] is not None
    # Visualizer suggestion for two-pointers
    assert data["visualization_suggestion"] is not None
    assert data["visualization_suggestion"]["visualizer_type"] == "two-pointers"


@pytest.mark.asyncio
async def test_ai_hint_progressive_disclosure(client: AsyncClient):
    token = await get_user_token(client, "student_hints@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch valid problem ID
    async with async_session_factory() as session:
        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()
        prob_id = prob.id

    # Test Level 1
    res1 = await client.post(
        "/api/v1/ai/hint",
        json={"problem_id": prob_id, "hint_level": 1},
        headers=headers,
    )
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["hint_level"] == 1
    assert d1["max_level"] == 5
    assert d1["is_last_hint"] is False

    # Test Level 5 (final level)
    res5 = await client.post(
        "/api/v1/ai/hint",
        json={"problem_id": prob_id, "hint_level": 5},
        headers=headers,
    )
    assert res5.status_code == 200
    d5 = res5.json()
    assert d5["hint_level"] == 5
    assert d5["is_last_hint"] is True

    # Invalid levels rejected by Pydantic validation (422)
    res_bad = await client.post(
        "/api/v1/ai/hint",
        json={"problem_id": prob_id, "hint_level": 6},
        headers=headers,
    )
    assert res_bad.status_code == 422


@pytest.mark.asyncio
async def test_ai_complexity_analyzer(client: AsyncClient):
    token = await get_user_token(client, "student_comp@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    code = """
def has_duplicate(nums):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] == nums[j]:
                return True
    return False
"""
    res = await client.post("/api/v1/ai/complexity", json={"code": code}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["time_complexity"] == "O(n^2)"
    assert data["confidence"] == "HIGH"
    assert "best_case" in data
    assert "worst_case" in data


@pytest.mark.asyncio
async def test_ai_pattern_detector(client: AsyncClient):
    token = await get_user_token(client, "student_pattern@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/ai/pattern",
        json={
            "problem_description": "Given an array of integers, find the contiguous subarray which has the largest sum.",
        },
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["primary_pattern"] in ["Sliding Window", "Dynamic Programming", "Linear Scan / Simulation"]
    assert len(data["evidence"]) >= 1


@pytest.mark.asyncio
async def test_ai_recommendations_with_and_without_user_history(client: AsyncClient):
    # 1. New user with NO history -> insufficient data state with starter suggestions
    new_user_token = await get_user_token(client, "new_learner_ai@example.com")
    res1 = await client.get("/api/v1/ai/recommendations", headers={"Authorization": f"Bearer {new_user_token}"})
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["has_sufficient_data"] is False
    assert len(d1["recommendations"]) >= 1

    # 2. User WITH attempts and mistakes -> personalized focus topics
    learner_token = await get_user_token(client, "experienced_learner_ai@example.com")
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "experienced_learner_ai@example.com"))).scalar_one()
        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        # Record failed attempt
        prog = UserProblemProgress(
            user_id=user.id,
            problem_id=prob.id,
            status=ProblemProgressStatus.ATTEMPTED,
            attempts_count=3,
        )
        # Record mistake
        mistake = Mistake(
            user_id=user.id,
            problem_id=prob.id,
            mistake_type=MistakeType.EDGE_CASE,
            title="Index bound error",
            description="Forgot index bound in loop",
        )


        session.add_all([prog, mistake])
        await session.commit()

    res2 = await client.get("/api/v1/ai/recommendations", headers={"Authorization": f"Bearer {learner_token}"})
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["has_sufficient_data"] is True
    assert len(d2["recommendations"]) >= 1
    assert any(w["topic_id"] == "cognitive-focus" for w in d2["weak_topics"])


@pytest.mark.asyncio
async def test_ai_usage_and_quota_tracking(client: AsyncClient):
    token = await get_user_token(client, "student_quota@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res_usage = await client.get("/api/v1/ai/usage", headers=headers)
    assert res_usage.status_code == 200
    u = res_usage.json()
    assert u["daily_quota"] > 0
    assert u["daily_remaining"] > 0
    assert u["can_request"] is True


@pytest.mark.asyncio
async def test_ai_hint_by_slug_and_tracking(client: AsyncClient):
    """Verifies requesting hints via problem slug works and records AIHintUsage."""
    token = await get_user_token(client, "student_slug_hint@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Request hint using problem slug directly
    res = await client.post(
        "/api/v1/ai/hint",
        json={"problem_id": "two-sum-seed", "hint_level": 2},
        headers=headers,
    )
    assert res.status_code == 200
    hint_data = res.json()
    assert hint_data["hint_level"] == 2
    assert "hint_content" in hint_data

    # Verify AIHintUsage record was persisted in database
    async with async_session_factory() as session:
        user_obj = (await session.execute(select(User).where(User.email == "student_slug_hint@example.com"))).scalar_one()
        logs = (await session.execute(select(AIHintUsage).where(AIHintUsage.user_id == user_obj.id))).scalars().all()
        assert len(logs) >= 1
        assert logs[-1].hint_level == 2
        assert logs[-1].number_of_hints_used >= 1


@pytest.mark.asyncio
async def test_ai_explain_with_submission_diagnostics(client: AsyncClient):
    """Verifies that explain_content enriches diagnostic explanations with real submission records."""
    token = await get_user_token(client, "student_explain_sub@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    async with async_session_factory() as session:
        user_obj = (await session.execute(select(User).where(User.email == "student_explain_sub@example.com"))).scalar_one()
        prob_obj = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        sub = Submission(
            user_id=user_obj.id,
            problem_id=prob_obj.id,
            language="python",
            source_code="def two_sum():\n    return []",
            status=SubmissionStatus.WRONG_ANSWER,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        sub_id = sub.id

    res = await client.post(
        "/api/v1/ai/explain",
        json={
            "target_type": "judge_error",
            "context_text": "Code returned [] instead of expected pair indices [0, 1].",
            "submission_id": sub_id,
            "problem_id": prob_obj.id,
        },
        headers=headers,
    )
    assert res.status_code == 200
    exp = res.json()
    assert "explanation" in exp
    assert len(exp["breakdown_points"]) >= 1


@pytest.mark.asyncio
async def test_gemini_provider_diagnostics(monkeypatch):
    """Verifies GeminiProvider diagnostics reports honest status when API key is missing or configured."""
    from backend.app.ai.providers.gemini_provider import GeminiProvider
    from backend.app.core.config import settings

    # Test when API key is missing
    monkeypatch.setattr(settings, "GOOGLE_AI_API_KEY", "")
    provider = GeminiProvider()
    diag = provider.get_diagnostics()
    assert diag["provider"] == "gemini"
    assert "BLOCKED — GOOGLE_AI_API_KEY REQUIRED" in diag["status"]
    assert provider.is_available() is False

    # Test when API key is configured
    monkeypatch.setattr(settings, "GOOGLE_AI_API_KEY", "valid_test_api_key_12345")
    provider_configured = GeminiProvider()
    diag_configured = provider_configured.get_diagnostics()
    assert diag_configured["status"] == "READY"
    assert provider_configured.is_available() is True


@pytest.mark.asyncio
async def test_ai_safe_fallback_on_provider_error(client: AsyncClient):
    """Verifies that if the live AI provider fails, AIService safely falls back to mock provider."""
    from backend.app.ai.providers.gemini_provider import GeminiProvider
    from backend.app.ai.providers import set_ai_provider_instance

    token = await get_user_token(client, "fallback_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    class FailingGeminiProvider(GeminiProvider):
        def get_diagnostics(self):
            return {"provider": "gemini", "model": "failing-gemini", "status": "READY"}

        async def tutor(self, *args, **kwargs):
            raise RuntimeError("Simulated Gemini 503 / 429 spike outage")

    set_ai_provider_instance(FailingGeminiProvider())

    try:
        res = await client.post(
            "/api/v1/ai/tutor",
            json={"question": "How does quicksort partition work?"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert "explanation" in data
        assert "key_idea" in data
    finally:
        set_ai_provider_instance(None)


