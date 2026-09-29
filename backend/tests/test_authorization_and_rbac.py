"""Authorization tests covering RBAC tiers, privilege escalation barriers, and IDOR protection."""

import pytest
from fastapi import Depends
from httpx import AsyncClient
from backend.app.api.deps import require_admin
from backend.app.main import app
from backend.app.models.user import User


# Register a temporary test route guarded by require_admin
@app.get("/test-admin-only-gate")
async def admin_gate(current_user: User = Depends(require_admin)):
    return {"admin_access": True}


@pytest.mark.asyncio
async def test_student_forbidden_from_admin_endpoint(client: AsyncClient):
    """Students accessing ADMIN-only endpoints must receive 403 Forbidden."""
    reg_payload = {
        "email": "student_rbac@example.com",
        "password": "Password123",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = res.json()["data"]["access_token"]

    admin_res = await client.get(
        "/test-admin-only-gate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert admin_res.status_code == 403
    data = admin_res.json()
    assert data["success"] is False
    assert "not permitted" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_vertical_privilege_escalation_blocked(client: AsyncClient):
    """Students cannot elevate their role to ADMIN via profile update."""
    reg_payload = {
        "email": "escalation_target@example.com",
        "password": "Password123",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = res.json()["data"]["access_token"]

    # Attempt to inject role field
    update_res = await client.put(
        "/api/v1/users/me/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "ADMIN", "display_name": "Hacked Name"},
    )
    # Extra fields must be forbidden by Pydantic schema
    assert update_res.status_code == 422


@pytest.mark.asyncio
async def test_idor_protection_on_payment_orders(client: AsyncClient):
    """User A must be forbidden from inspecting User B's payment order."""
    # Register User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "password": "Password123"},
    )
    token_a = res_a.json()["data"]["access_token"]

    # Register User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "password": "Password123"},
    )
    token_b = res_b.json()["data"]["access_token"]

    # User B creates an order
    order_b_res = await client.post(
        "/api/v1/payments/create-order",
        headers={"Authorization": f"Bearer {token_b}"},
        json={},
    )
    assert order_b_res.status_code == 201
    order_b_id = order_b_res.json()["data"]["order_id"]

    # User A attempts to view User B's order
    attack_res = await client.get(
        f"/api/v1/payments/{order_b_id}/status",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert attack_res.status_code == 403
    data = attack_res.json()
    assert data["success"] is False
    assert "not authorized" in data["error"]["message"].lower()
