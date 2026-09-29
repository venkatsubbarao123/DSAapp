"""Security tests for Phase 4: Cross-user IDOR prevention, privacy, mass assignment, and Premium gates."""

from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient

from backend.app.core.security import create_access_token
from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.models.payment import EntitlementStatus, PremiumEntitlement
from backend.app.models.user import User, UserRole


@pytest.fixture(autouse=True)
async def seed_data():
    """Seeds verified content before running security tests."""
    async with async_session_factory() as session:
        await seed_development_content(session)


async def register_user(client: AsyncClient, email: str) -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    return res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_idor_submission_cross_user_access_blocked(client: AsyncClient):
    """User B cannot access or view User A's private code submission."""
    token_a = await register_user(client, "user_a_sub@example.com")
    token_b = await register_user(client, "user_b_sub@example.com")

    # User A creates a submission
    create_res = await client.post(
        "/api/v1/submissions",
        json={"problem_id": "two-sum-seed", "language": "python", "source_code": "secret_user_a_code = 1"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    sub_id = create_res.json()["data"]["id"]

    # User B tries to access User A's submission
    res_b = await client.get(
        f"/api/v1/submissions/{sub_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 404
    assert res_b.json()["success"] is False


@pytest.mark.asyncio
async def test_idor_mistake_cross_user_access_and_mutation_blocked(client: AsyncClient):
    """User B cannot view, edit, or delete User A's personal mistake notebook records."""
    token_a = await register_user(client, "user_a_mst@example.com")
    token_b = await register_user(client, "user_b_mst@example.com")

    # User A creates mistake
    create_res = await client.post(
        "/api/v1/mistakes",
        json={"title": "Private Concept Gap", "description": "User A secret notes", "mistake_type": "CONCEPT_GAP"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    mst_id = create_res.json()["data"]["id"]

    # 1. User B tries to read
    assert (await client.get(f"/api/v1/mistakes/{mst_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404

    # 2. User B tries to update
    assert (await client.patch(f"/api/v1/mistakes/{mst_id}", json={"title": "Hacked"}, headers={"Authorization": f"Bearer {token_b}"})).status_code == 404

    # 3. User B tries to delete
    assert (await client.delete(f"/api/v1/mistakes/{mst_id}", headers={"Authorization": f"Bearer {token_b}"})).status_code == 404


@pytest.mark.asyncio
async def test_idor_revision_review_cross_user_blocked(client: AsyncClient):
    """User B cannot submit review outcomes for User A's revision item."""
    token_a = await register_user(client, "user_a_rev@example.com")
    token_b = await register_user(client, "user_b_rev@example.com")

    item_res = await client.post(
        "/api/v1/revision",
        json={"source_type": "PROBLEM", "source_id": "two-sum-seed", "title": "User A Revision"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    item_id = item_res.json()["data"]["id"]

    res_b = await client.post(
        f"/api/v1/revision/{item_id}/review",
        json={"outcome": "EASY"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 404


@pytest.mark.asyncio
async def test_progress_privacy_isolation_between_users(client: AsyncClient):
    """User B querying problem progress sees only their own status, isolated from User A."""
    token_a = await register_user(client, "user_a_prog@example.com")
    token_b = await register_user(client, "user_b_prog@example.com")

    # User A solves problem
    await client.post(
        "/api/v1/progress/problems/two-sum-seed/solve",
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B queries problem progress
    res_b = await client.get(
        "/api/v1/progress/problems/two-sum-seed",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 200
    prog_b = res_b.json()["data"]
    assert prog_b["status"] == "NOT_STARTED"
    assert prog_b["successful_attempts"] == 0


@pytest.mark.asyncio
async def test_mass_assignment_protection_on_submissions_and_mistakes(client: AsyncClient):
    """Payloads attempting injection of internal fields (user_id, status, is_admin) are rejected."""
    token = await register_user(client, "mass_assign@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Submission payload with injected user_id and status
    malicious_sub = {
        "problem_id": "two-sum-seed",
        "language": "python",
        "source_code": "x = 1",
        "user_id": "victim-user-id",
        "status": "ACCEPTED",
    }
    res_sub = await client.post("/api/v1/submissions", json=malicious_sub, headers=headers)
    assert res_sub.status_code == 422

    # 2. Mistake payload with injected user_id and is_resolved
    malicious_mst = {
        "title": "Exploit Test",
        "description": "Exploit description",
        "mistake_type": "OTHER",
        "user_id": "victim-user-id",
    }
    res_mst = await client.post("/api/v1/mistakes", json=malicious_mst, headers=headers)
    assert res_mst.status_code == 422


@pytest.mark.asyncio
async def test_premium_gate_on_mastery_insights(client: AsyncClient):
    """Free user receives 403 on Mastery Insights; active Premium user receives 200 OK."""
    # 1. Free user
    token_free = await register_user(client, "free_mastery@example.com")
    res_free = await client.get("/api/v1/progress/mastery", headers={"Authorization": f"Bearer {token_free}"})
    assert res_free.status_code == 403

    # 2. Premium user
    async with async_session_factory() as session:
        pro_user = User(
            email="premium_mastery@example.com",
            hashed_password="argon2id$mockhash",
            role=UserRole.STUDENT,
            is_active=True,
        )
        session.add(pro_user)
        await session.flush()

        entitlement = PremiumEntitlement(
            user_id=pro_user.id,
            status=EntitlementStatus.ACTIVE,
            activated_at=datetime.now(timezone.utc) - timedelta(days=1),
            expires_at=datetime.now(timezone.utc) + timedelta(days=364),
        )
        session.add(entitlement)
        await session.commit()
        pro_token = create_access_token(pro_user.id, pro_user.role.value)

    res_pro = await client.get("/api/v1/progress/mastery", headers={"Authorization": f"Bearer {pro_token}"})
    assert res_pro.status_code == 200
    assert res_pro.json()["success"] is True
    assert "spaced_retention_score" in res_pro.json()["data"]


@pytest.mark.asyncio
async def test_unauthenticated_requests_rejected(client: AsyncClient):
    """All Phase 4 endpoints strictly require authentication."""
    assert (await client.get("/api/v1/progress/overview")).status_code == 401
    assert (await client.get("/api/v1/submissions")).status_code == 401
    assert (await client.get("/api/v1/mistakes")).status_code == 401
    assert (await client.get("/api/v1/revision")).status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_defense_in_mistake_search(client: AsyncClient):
    """SQL injection strings in search parameters are safely parameterized."""
    token = await register_user(client, "sqli_search@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    sqli_term = "' OR '1'='1' --"
    res = await client.get(f"/api/v1/mistakes?search={sqli_term}", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 0
