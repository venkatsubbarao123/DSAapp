"""Tests for learning progress tracking: lessons, problems, topics, and overview metrics."""

import pytest
from httpx import AsyncClient

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory


@pytest.fixture(autouse=True)
async def seed_data():
    """Seeds verified content before running progress tests."""
    async with async_session_factory() as session:
        await seed_development_content(session)


async def register_and_get_token(client: AsyncClient, email: str = "progress_user@example.com") -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    return res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_lesson_start_and_completion_flow(client: AsyncClient):
    """User can start a lesson and complete it, updating progress percentage to 100%."""
    token = await register_and_get_token(client, "lesson_student@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Start lesson
    start_res = await client.post("/api/v1/progress/lessons/dynamic-arrays-seed/start", headers=headers)
    assert start_res.status_code == 200
    start_data = start_res.json()["data"]
    assert start_data["status"] == "IN_PROGRESS"
    assert start_data["progress_percent"] == 25
    assert start_data["started_at"] is not None
    assert start_data["completed_at"] is None

    # 2. Complete lesson
    comp_res = await client.post("/api/v1/progress/lessons/dynamic-arrays-seed/complete", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["progress_percent"] == 100
    assert comp_data["completed_at"] is not None


@pytest.mark.asyncio
async def test_nonexistent_or_unpublished_lesson_rejected(client: AsyncClient):
    """Starting or completing nonexistent lesson returns 404."""
    token = await register_and_get_token(client, "ghost_student@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post("/api/v1/progress/lessons/nonexistent-lesson-uuid/start", headers=headers)
    assert res.status_code == 404
    assert res.json()["success"] is False


@pytest.mark.asyncio
async def test_problem_attempt_and_solve_flow(client: AsyncClient):
    """User can record problem attempt and verified solve."""
    token = await register_and_get_token(client, "problem_student@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Record attempt
    att_res = await client.post("/api/v1/progress/problems/two-sum-seed/attempt", headers=headers)
    assert att_res.status_code == 200
    att_data = att_res.json()["data"]
    assert att_data["status"] == "ATTEMPTED"
    assert att_data["attempts_count"] == 1
    assert att_data["successful_attempts"] == 0

    # 2. Repeated attempt
    att_res2 = await client.post("/api/v1/progress/problems/two-sum-seed/attempt", headers=headers)
    assert att_res2.status_code == 200
    assert att_res2.json()["data"]["attempts_count"] == 2

    # 3. Solve problem
    solve_res = await client.post("/api/v1/progress/problems/two-sum-seed/solve", headers=headers)
    assert solve_res.status_code == 200
    solve_data = solve_res.json()["data"]
    assert solve_data["status"] == "SOLVED"
    assert solve_data["successful_attempts"] == 1
    assert solve_data["solved_at"] is not None


@pytest.mark.asyncio
async def test_progress_overview_aggregates_real_db_data(client: AsyncClient):
    """GET /api/v1/progress/overview calculates real counts without fake data."""
    token = await register_and_get_token(client, "overview_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Baseline before actions
    res_base = await client.get("/api/v1/progress/overview", headers=headers)
    assert res_base.status_code == 200
    data_base = res_base.json()["data"]
    assert data_base["lessons_completed"] == 0
    assert data_base["problems_solved"] == 0
    assert data_base["overall_completion_percent"] == 0.0

    # User completes 1 lesson and solves 1 problem
    await client.post("/api/v1/progress/lessons/dynamic-arrays-seed/complete", headers=headers)
    await client.post("/api/v1/progress/problems/two-sum-seed/solve", headers=headers)

    res_updated = await client.get("/api/v1/progress/overview", headers=headers)
    assert res_updated.status_code == 200
    data_up = res_updated.json()["data"]
    assert data_up["lessons_completed"] == 1
    assert data_up["problems_solved"] == 1
    assert data_up["overall_completion_percent"] > 0.0
    assert len(data_up["recent_activity"]) >= 2


@pytest.mark.asyncio
async def test_topic_progress_calculation(client: AsyncClient):
    """GET /api/v1/progress/topics/{topic_id} aggregates child lessons and problems."""
    token = await register_and_get_token(client, "topic_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch arrays topic progress
    res = await client.get("/api/v1/progress/topics/arrays-seed", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["topic_slug"] == "arrays-seed"
    assert data["total_lessons"] >= 1
    assert data["total_problems"] >= 1
    assert data["completed_lessons"] == 0
    assert data["solved_problems"] == 0

    # Complete a lesson
    await client.post("/api/v1/progress/lessons/dynamic-arrays-seed/complete", headers=headers)

    res2 = await client.get("/api/v1/progress/topics/arrays-seed", headers=headers)
    data2 = res2.json()["data"]
    assert data2["completed_lessons"] == 1
    assert data2["completion_percent"] > 0.0
