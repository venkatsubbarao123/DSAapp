"""Unit and integration tests for Competitive Programming Arena and OOP Module."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.security import create_access_token
from backend.app.models.content import (
    ContentAccessLevel,
    ContentLevel,
    ContentStatus as ProbStatus,
    Problem,
    ProblemDifficulty,
)
from backend.app.models.cp import CPProblemMetadata, CompetitiveRating
from backend.app.models.user import User, UserRole
from backend.app.services.cp.cp_service import CPService
from backend.app.services.oop.oop_service import OOPService


@pytest.fixture
async def cp_test_data(db_session: AsyncSession):
    """Sets up test problem, CP metadata, and users."""
    uid = uuid.uuid4().hex[:6]

    user = User(
        email=f"cp_coder_{uid}@example.com",
        hashed_password="hashed_pwd",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    prob = Problem(
        title=f"Segment Tree Range Query {uid}",
        slug=f"segment-tree-query-{uid}",
        statement="Answer point update and range sum queries in O(log N).",
        difficulty=ProblemDifficulty.HARD,
        status=ProbStatus.PUBLISHED,
        access_level=ContentAccessLevel.FREE,
        display_order=1,
    )
    db_session.add(prob)
    await db_session.flush()

    cp_meta = CPProblemMetadata(
        problem_id=prob.id,
        rating_band=1900,
        time_limit_ms=1500,
        memory_limit_mb=256,
        input_format="First line: N and Q. Next line: N integers.",
        output_format="For each query, output the range sum.",
        constraints="1 <= N, Q <= 200,000",
        editorial="Use a 1-based segment tree with binary representation.",
    )
    db_session.add(cp_meta)
    await db_session.commit()

    return {"user": user, "problem": prob, "cp_meta": cp_meta}


@pytest.mark.asyncio
async def test_cp_problem_catalog_and_detail(
    client: AsyncClient,
    cp_test_data: dict,
):
    """Verifies CP problem filtering by rating band and complete detail payload."""
    prob = cp_test_data["problem"]
    meta = cp_test_data["cp_meta"]

    # 1. Filter problems by rating band 1900
    res = await client.get("/api/v1/competitive/problems?rating_band=1900")
    assert res.status_code == 200
    problems = res.json()
    assert len(problems) >= 1
    found = any(p["slug"] == prob.slug for p in problems)
    assert found is True

    # 2. Filter by different rating band
    res_other = await client.get("/api/v1/competitive/problems?rating_band=800")
    assert res_other.status_code == 200
    assert not any(p["slug"] == prob.slug for p in res_other.json())

    # 3. Get CP problem detail
    detail_res = await client.get(f"/api/v1/competitive/problems/{prob.slug}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["rating_band"] == 1900
    assert detail["input_format"] == meta.input_format
    assert detail["constraints"] == meta.constraints


@pytest.mark.asyncio
async def test_cp_rating_and_leaderboard(
    client: AsyncClient,
    db_session: AsyncSession,
    cp_test_data: dict,
):
    """Verifies competitive rating adjustments, titles, and leaderboard ranking."""
    user = cp_test_data["user"]
    token = create_access_token(user_id=user.id, role=user.role.value)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial profile: 1200 rating (Pupil)
    profile_res = await client.get("/api/v1/competitive/profile", headers=headers)
    assert profile_res.status_code == 200
    prof = profile_res.json()
    assert prof["current_rating"] == 1200
    assert prof["rank_title"] == "Pupil"

    # 2. Server-authoritatively adjust rating after contest (+450) -> 1650 (Expert)
    new_rating = await CPService.adjust_rating(
        db=db_session,
        user_id=user.id,
        delta=450,
        reason="CONTEST_WIN",
    )
    assert new_rating == 1650

    # 3. Check profile updated
    profile_res2 = await client.get("/api/v1/competitive/profile", headers=headers)
    assert profile_res2.status_code == 200
    prof2 = profile_res2.json()
    assert prof2["current_rating"] == 1650
    assert prof2["rank_title"] == "Expert"

    # 4. Check CP leaderboard
    lb_res = await client.get("/api/v1/competitive/leaderboard")
    assert lb_res.status_code == 200
    lb = lb_res.json()
    assert lb["total"] >= 1
    assert lb["entries"][0]["current_rating"] >= 1200


@pytest.mark.asyncio
async def test_oop_module_catalog_and_detail(client: AsyncClient):
    """Verifies structured OOP modules covering Pillars, SOLID, and Design Patterns."""
    # 1. List modules
    list_res = await client.get("/api/v1/oop/modules")
    assert list_res.status_code == 200
    modules = list_res.json()
    assert len(modules) >= 5

    categories = {m["category"] for m in modules}
    assert "PILLARS" in categories
    assert "SOLID" in categories
    assert "DESIGN_PATTERNS" in categories

    # 2. Get specific module detail
    mod_id = modules[0]["id"]
    det_res = await client.get(f"/api/v1/oop/modules/{mod_id}")
    assert det_res.status_code == 200
    detail = det_res.json()
    assert "code_example" in detail
    assert "key_concepts" in detail
    assert len(detail["key_concepts"]) > 0
