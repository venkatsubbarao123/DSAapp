"""Tests for personal mistake notebook and spaced revision queue."""

import pytest
from httpx import AsyncClient

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory


@pytest.fixture(autouse=True)
async def seed_data():
    """Seeds verified content before running mistake tests."""
    async with async_session_factory() as session:
        await seed_development_content(session)


async def register_and_get_token(client: AsyncClient, email: str = "mistake_user@example.com") -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    return res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_mistake_crud_lifecycle(client: AsyncClient):
    """Learner can create, read, update, resolve, and delete personal mistake notes."""
    token = await register_and_get_token(client, "crud_mistake@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create mistake
    payload = {
        "title": "Forgot duplicate element handling",
        "description": "Inner loop missed duplicates when sorting.",
        "mistake_type": "EDGE_CASE",
        "problem_id": "two-sum-seed",
    }
    create_res = await client.post("/api/v1/mistakes", json=payload, headers=headers)
    assert create_res.status_code == 201
    mistake = create_res.json()["data"]
    m_id = mistake["id"]
    assert mistake["title"] == payload["title"]
    assert mistake["mistake_type"] == "EDGE_CASE"
    assert mistake["is_resolved"] is False
    assert mistake["problem_slug"] == "two-sum-seed"

    # 2. Update / Resolve mistake
    patch_res = await client.patch(
        f"/api/v1/mistakes/{m_id}",
        json={"is_resolved": True, "correction": "Skip identical adjacent items."},
        headers=headers,
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()["data"]
    assert patched["is_resolved"] is True
    assert patched["resolved_at"] is not None
    assert patched["correction"] == "Skip identical adjacent items."

    # 3. Read single mistake
    get_res = await client.get(f"/api/v1/mistakes/{m_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == m_id

    # 4. Delete mistake
    del_res = await client.delete(f"/api/v1/mistakes/{m_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True

    # 5. Subsequent get returns 404
    assert (await client.get(f"/api/v1/mistakes/{m_id}", headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_mistakes_filtering_and_search(client: AsyncClient):
    """Mistake notebook supports filtering by category, resolution, and search."""
    token = await register_and_get_token(client, "filter_mistake@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create two mistakes
    await client.post(
        "/api/v1/mistakes",
        json={"title": "Off by one indexing", "description": "Loop exceeded bounds", "mistake_type": "LOGIC_ERROR"},
        headers=headers,
    )
    await client.post(
        "/api/v1/mistakes",
        json={"title": "Hash collision misconception", "description": "Assumed no collision", "mistake_type": "CONCEPT_GAP"},
        headers=headers,
    )

    # Filter by type
    res_type = await client.get("/api/v1/mistakes?mistake_type=LOGIC_ERROR", headers=headers)
    assert res_type.status_code == 200
    assert len(res_type.json()["data"]["items"]) == 1
    assert res_type.json()["data"]["items"][0]["mistake_type"] == "LOGIC_ERROR"

    # Search by keyword
    res_search = await client.get("/api/v1/mistakes?search=collision", headers=headers)
    assert res_search.status_code == 200
    assert len(res_search.json()["data"]["items"]) == 1
    assert "collision" in res_search.json()["data"]["items"][0]["description"].lower()


@pytest.mark.asyncio
async def test_revision_item_creation_and_due_queue(client: AsyncClient):
    """Creating revision items establishes spaced schedules and lists in due queue."""
    token = await register_and_get_token(client, "revision_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create revision item for a problem
    payload = {
        "source_type": "PROBLEM",
        "source_id": "two-sum-seed",
        "title": "Two Sum Spaced Review",
        "priority": 2,
    }
    create_res = await client.post("/api/v1/revision", json=payload, headers=headers)
    assert create_res.status_code == 201
    item = create_res.json()["data"]
    assert item["source_type"] == "PROBLEM"
    assert item["schedule"] is not None
    assert item["schedule"]["interval_days"] == 1.0

    # List queue
    queue_res = await client.get("/api/v1/revision", headers=headers)
    assert queue_res.status_code == 200
    queue_items = queue_res.json()["data"]["items"]
    assert len(queue_items) == 1
    assert queue_items[0]["id"] == item["id"]


@pytest.mark.asyncio
async def test_revision_review_outcomes_and_intervals(client: AsyncClient):
    """Reviewing revision item with outcomes updates interval deterministically."""
    token = await register_and_get_token(client, "review_calc_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    item_res = await client.post(
        "/api/v1/revision",
        json={"source_type": "LESSON", "source_id": "dynamic-arrays-seed", "title": "Dynamic Arrays Review"},
        headers=headers,
    )
    item_id = item_res.json()["data"]["id"]

    # 1. Review GOOD (increases interval by ease factor 2.5)
    review_res = await client.post(
        f"/api/v1/revision/{item_id}/review",
        json={"outcome": "GOOD"},
        headers=headers,
    )
    assert review_res.status_code == 200
    sched = review_res.json()["data"]["schedule"]
    assert sched["review_count"] == 1
    assert sched["interval_days"] >= 2.0

    # 2. Review AGAIN (resets interval to short 0.5 days)
    again_res = await client.post(
        f"/api/v1/revision/{item_id}/review",
        json={"outcome": "AGAIN"},
        headers=headers,
    )
    assert again_res.status_code == 200
    sched_again = again_res.json()["data"]["schedule"]
    assert sched_again["review_count"] == 0
    assert sched_again["interval_days"] == 0.5
