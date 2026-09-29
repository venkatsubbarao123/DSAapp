"""Tests for Phase 6 AI endpoints, authorization, quotas, and personalized recommendations."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.models.content import Problem
from backend.app.models.progress import Mistake, MistakeType, ProblemProgressStatus, UserProblemProgress
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
