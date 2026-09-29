"""API tests for student curriculum, topics, lessons, problems, filtering, and hidden-test suppression."""

import pytest
from httpx import AsyncClient

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.models.content import ContentAccessLevel, ContentStatus, Problem, ProblemDifficulty


@pytest.fixture(autouse=True)
async def seed_data():
    """Seeds verified content before running API tests."""
    async with async_session_factory() as session:
        await seed_development_content(session)


@pytest.mark.asyncio
async def test_list_curricula_and_detail(client: AsyncClient):
    """GET /api/v1/curricula returns list of published curricula; detail includes tracks."""
    res = await client.get("/api/v1/curricula")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
    slug = data["data"][0]["slug"]

    # Detail
    detail_res = await client.get(f"/api/v1/curricula/{slug}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["success"] is True
    assert len(detail_data["data"]["tracks"]) >= 1


@pytest.mark.asyncio
async def test_list_topics_and_pagination(client: AsyncClient):
    """GET /api/v1/topics supports safe pagination envelope."""
    res = await client.get("/api/v1/topics?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    paginated = data["data"]
    assert paginated["page"] == 1
    assert paginated["page_size"] == 10
    assert paginated["total"] >= 2
    assert len(paginated["items"]) >= 2


@pytest.mark.asyncio
async def test_get_topic_detail_with_subtopics(client: AsyncClient):
    """GET /api/v1/topics/{slug} returns topic and nested subtopics."""
    res = await client.get("/api/v1/topics/arrays-seed")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["slug"] == "arrays-seed"
    assert len(data["data"]["subtopics"]) >= 1


@pytest.mark.asyncio
async def test_get_free_lesson_structured_blocks(client: AsyncClient):
    """GET /api/v1/lessons/{slug} returns safe structured blocks (XSS immune)."""
    res = await client.get("/api/v1/lessons/dynamic-arrays-seed")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    lesson = data["data"]
    assert lesson["slug"] == "dynamic-arrays-seed"
    assert len(lesson["blocks"]) >= 2
    assert any(b["type"] == "code" for b in lesson["blocks"])


@pytest.mark.asyncio
async def test_problem_listing_filtering_and_search(client: AsyncClient):
    """GET /api/v1/problems supports difficulty, topic, tag, pattern, and keyword search."""
    # Filter by EASY
    res_easy = await client.get("/api/v1/problems?difficulty=EASY")
    assert res_easy.status_code == 200
    data_easy = res_easy.json()["data"]["items"]
    assert all(p["difficulty"] == "EASY" for p in data_easy)

    # Search keyword
    res_search = await client.get("/api/v1/problems?search=Two+Sum")
    assert res_search.status_code == 200
    items = res_search.json()["data"]["items"]
    assert len(items) >= 1
    assert any("Two Sum" in p["title"] for p in items)


@pytest.mark.asyncio
async def test_get_problem_detail_and_hidden_test_cases_suppression(client: AsyncClient):
    """GET /api/v1/problems/{slug} returns problem details while strictly suppressing hidden test cases."""
    res = await client.get("/api/v1/problems/two-sum-seed")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    prob = data["data"]
    assert prob["slug"] == "two-sum-seed"
    assert len(prob["examples"]) >= 1
    assert len(prob["hints"]) >= 2

    # SECURITY INVARIANT TEST:
    # Problem 1 has 1 sample testcase and 1 hidden testcase in the DB.
    # The API must expose ONLY sample test cases and NEVER hidden test cases!
    sample_cases = prob["sample_test_cases"]
    assert len(sample_cases) == 1
    assert sample_cases[0]["is_sample"] is True
    # Ensure hidden test case input "[3, 2, 4]" is NOT leaked
    assert "[3, 2, 4]" not in str(data)
    assert "is_hidden" not in str(sample_cases)


@pytest.mark.asyncio
async def test_unpublished_draft_content_hidden_from_students(client: AsyncClient):
    """DRAFT and REVIEW content must never appear in student APIs."""
    async with async_session_factory() as session:
        draft_problem = Problem(
            slug="secret-draft-problem",
            title="Secret Draft Problem",
            statement="Draft statement",
            difficulty=ProblemDifficulty.HARD,
            access_level=ContentAccessLevel.FREE,
            status=ContentStatus.DRAFT,  # DRAFT!
        )
        session.add(draft_problem)
        await session.commit()

    # Listing must NOT include draft problem
    res_list = await client.get("/api/v1/problems")
    slugs = [p["slug"] for p in res_list.json()["data"]["items"]]
    assert "secret-draft-problem" not in slugs

    # Direct detail access must return 404 for students
    res_detail = await client.get("/api/v1/problems/secret-draft-problem")
    assert res_detail.status_code == 404
