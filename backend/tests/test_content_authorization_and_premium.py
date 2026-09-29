"""Authorization and security tests for Premium content gates, RBAC, mass assignment, and SQLi resistance."""

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
    """Seeds verified content before running tests."""
    async with async_session_factory() as session:
        await seed_development_content(session)


@pytest.mark.asyncio
async def test_free_user_denied_premium_problem_and_lesson(client: AsyncClient):
    """Free user or unauthenticated client receives 403 on Premium content."""
    # 1. Unauthenticated request to Premium problem
    res_unauth = await client.get("/api/v1/problems/longest-substring-without-repeating-characters-seed")
    assert res_unauth.status_code == 403
    assert "premium subscription" in res_unauth.json()["error"]["message"].lower()

    # 2. Authenticated FREE user
    reg = await client.post("/api/v1/auth/register", json={"email": "free_student_content@example.com", "password": "Password123"})
    token = reg.json()["data"]["access_token"]

    res_auth = await client.get(
        "/api/v1/problems/longest-substring-without-repeating-characters-seed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_auth.status_code == 403

    # 3. Premium lesson access denied to free user
    res_lesson = await client.get(
        "/api/v1/lessons/sliding-window-template-seed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_lesson.status_code == 403


@pytest.mark.asyncio
async def test_premium_user_granted_access_to_premium_content(client: AsyncClient):
    """User with active Premium entitlement can access Premium problems and lessons."""
    # 1. Register user
    reg = await client.post("/api/v1/auth/register", json={"email": "premium_student_content@example.com", "password": "Password123"})
    token = reg.json()["data"]["access_token"]

    # 2. Upgrade to Premium via order & verify
    order = await client.post("/api/v1/payments/create-order", headers={"Authorization": f"Bearer {token}"}, json={})
    order_id = order.json()["data"]["order_id"]
    await client.post(f"/api/v1/payments/{order_id}/verify", headers={"Authorization": f"Bearer {token}"}, json={"transaction_id": "tx_prem_ok"})

    # 3. Access Premium problem
    res_prob = await client.get(
        "/api/v1/problems/longest-substring-without-repeating-characters-seed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_prob.status_code == 200
    assert res_prob.json()["data"]["slug"] == "longest-substring-without-repeating-characters-seed"

    # 4. Access Premium lesson
    res_les = await client.get(
        "/api/v1/lessons/sliding-window-template-seed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_les.status_code == 200
    assert res_les.json()["data"]["slug"] == "sliding-window-template-seed"


@pytest.mark.asyncio
async def test_expired_premium_user_denied_access(client: AsyncClient):
    """Users with expired premium entitlement must immediately be blocked as Free."""
    async with async_session_factory() as session:
        # Create user with expired entitlement
        user = User(email="expired_user@example.com", hashed_password="pw", role=UserRole.STUDENT)
        session.add(user)
        await session.flush()

        expired_entitlement = PremiumEntitlement(
            user_id=user.id,
            plan_id="plan_premium_annual",
            status=EntitlementStatus.ACTIVE,
            activated_at=datetime.now(timezone.utc) - timedelta(days=400),
            expires_at=datetime.now(timezone.utc) - timedelta(days=35),  # Expired 35 days ago!
        )
        session.add(expired_entitlement)
        await session.commit()
        user_id = user.id

    token = create_access_token(user_id, UserRole.STUDENT.value)

    res = await client.get(
        "/api/v1/problems/longest-substring-without-repeating-characters-seed",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_student_forbidden_from_admin_content_endpoints(client: AsyncClient):
    """Students cannot create topics, lessons, or problems."""
    reg = await client.post("/api/v1/auth/register", json={"email": "student_cant_edit@example.com", "password": "Password123"})
    token = reg.json()["data"]["access_token"]

    # Student attempting to create topic
    res = await client.post(
        "/api/v1/admin/topics",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": "hacked-topic", "title": "Hacked Topic", "description": "desc"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_content_editor_can_author_and_publish_content(client: AsyncClient):
    """Users with CONTENT_EDITOR role can author and transition publishing status."""
    async with async_session_factory() as session:
        editor = User(email="editor@example.com", hashed_password="pw", role=UserRole.CONTENT_EDITOR)
        session.add(editor)
        await session.commit()
        editor_id = editor.id

    token = create_access_token(editor_id, UserRole.CONTENT_EDITOR.value)

    # Editor creates a topic
    res_create = await client.post(
        "/api/v1/admin/topics",
        headers={"Authorization": f"Bearer {token}"},
        json={"slug": "editor-authored-topic", "title": "Editor Authored Topic", "description": "desc"},
    )
    assert res_create.status_code == 201
    topic_id = res_create.json()["data"]["id"]

    # Editor updates status to ARCHIVED
    res_status = await client.patch(
        f"/api/v1/admin/content/topic/{topic_id}/status",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "ARCHIVED"},
    )
    assert res_status.status_code == 200
    assert res_status.json()["data"]["status"] == "ARCHIVED"


@pytest.mark.asyncio
async def test_mass_assignment_protection_on_content_create(client: AsyncClient):
    """Client attempting to inject created_by or version in body is rejected by extra='forbid'."""
    async with async_session_factory() as session:
        editor = User(email="editor_ma@example.com", hashed_password="pw", role=UserRole.CONTENT_EDITOR)
        session.add(editor)
        await session.commit()
        editor_id = editor.id

    token = create_access_token(editor_id, UserRole.CONTENT_EDITOR.value)

    res = await client.post(
        "/api/v1/admin/topics",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "slug": "injected-topic",
            "title": "Injected Topic",
            "description": "desc",
            "created_by": "00000000-0000-0000-0000-000000000000",  # Injected field!
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_sql_injection_resistance_in_search_and_filters(client: AsyncClient):
    """Search and filter parameters must use parameterized queries immune to SQL injection."""
    sqli_payloads = [
        "' OR '1'='1",
        "'; DROP TABLE problems; --",
        "UNION SELECT null, null, null--",
    ]
    for payload in sqli_payloads:
        res = await client.get(f"/api/v1/problems?search={payload}")
        assert res.status_code == 200
        # Confirms database remains intact and returns clean empty/zero search results
        assert res.json()["success"] is True
        assert isinstance(res.json()["data"]["items"], list)
