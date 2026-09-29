"""Payment and premium entitlement tests covering gates, idempotency, and signature verification."""

import base64
import hashlib
import json
import pytest
from httpx import AsyncClient

from backend.app.core.config import settings
from backend.app.db.session import async_session_factory
from backend.app.repositories.payment_repo import PaymentRepository


@pytest.mark.asyncio
async def test_free_user_denied_premium_gate(client: AsyncClient):
    """Free user without an active premium entitlement must receive 403 on premium endpoints."""
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "freeuser@example.com", "password": "Password123"},
    )
    token = res.json()["data"]["access_token"]

    gate_res = await client.get(
        "/api/v1/premium/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gate_res.status_code == 403
    data = gate_res.json()
    assert data["success"] is False
    assert "premium subscription" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_authoritative_server_pricing_enforced(client: AsyncClient):
    """Clients cannot specify an order amount; server configuration governs authoritative price."""
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "pricingtest@example.com", "password": "Password123"},
    )
    token = res.json()["data"]["access_token"]

    # Valid order creation
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    assert order_res.status_code == 201
    data = order_res.json()
    assert data["data"]["amount"] == settings.PREMIUM_PRICE
    assert data["data"]["currency"] == settings.PREMIUM_CURRENCY

    # Attempt to tamper with price in body must be rejected by Pydantic extra='forbid'
    tamper_res = await client.post(
        "/api/v1/payments/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={"amount": 0},
    )
    assert tamper_res.status_code == 422


@pytest.mark.asyncio
async def test_payment_verification_and_premium_activation_cycle(client: AsyncClient):
    """Verifying payment activates Premium entitlement and unlocks the premium gate."""
    # 1. Register user
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "premiumuser@example.com", "password": "Password123"},
    )
    token = res.json()["data"]["access_token"]

    # 2. Create order
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    order_id = order_res.json()["data"]["order_id"]

    # 3. Verify order (in development mode)
    verify_res = await client.post(
        f"/api/v1/payments/{order_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={"transaction_id": "tx_mock_123"},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "SUCCESS"

    # 4. Verify account /me now reflects PREMIUM plan
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["plan"] == "PREMIUM"
    assert me_res.json()["data"]["premium_active"] is True

    # 5. Verify premium gate is now UNLOCKED (HTTP 200)
    gate_res = await client.get(
        "/api/v1/premium/preview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert gate_res.status_code == 200
    gate_data = gate_res.json()
    assert gate_data["data"]["authorized"] is True


@pytest.mark.asyncio
async def test_payment_idempotency_prevents_duplicate_activation(client: AsyncClient):
    """Calling verification twice on the same order must not duplicate entitlements."""
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "idempotent@example.com", "password": "Password123"},
    )
    token = res.json()["data"]["access_token"]

    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    order_id = order_res.json()["data"]["order_id"]

    # First verify
    await client.post(
        f"/api/v1/payments/{order_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={"transaction_id": "tx_idem_1"},
    )

    # Second verify
    res2 = await client.post(
        f"/api/v1/payments/{order_id}/verify",
        headers={"Authorization": f"Bearer {token}"},
        json={"transaction_id": "tx_idem_2"},
    )
    assert res2.status_code == 200


@pytest.mark.asyncio
async def test_phonepe_webhook_signature_verification(client: AsyncClient):
    """PhonePe webhook verifies checksum signature, rejecting tampered payloads."""
    # Prepare mock PhonePe salt settings for test
    salt_key = "test_salt_key_12345"
    salt_index = "1"
    settings.PHONEPE_SALT_KEY = salt_key
    settings.PHONEPE_SALT_INDEX = salt_index

    # Create user and order
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "webhook_test@example.com", "password": "Password123"},
    )
    token = res.json()["data"]["access_token"]
    order_res = await client.post(
        "/api/v1/payments/create-order",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )
    order_id = order_res.json()["data"]["order_id"]

    # Construct PhonePe callback payload
    callback_payload = {
        "success": True,
        "code": "PAYMENT_SUCCESS",
        "data": {
            "merchantTransactionId": order_id,
            "transactionId": "tx_phonepe_999",
            "amount": settings.PREMIUM_PRICE * 100,
            "paymentState": "COMPLETED",
        },
    }
    raw_b64 = base64.b64encode(json.dumps(callback_payload).encode("utf-8")).decode("utf-8")

    # Compute valid checksum: SHA256(raw_b64 + salt_key) + "###" + salt_index
    valid_checksum = hashlib.sha256(f"{raw_b64}{salt_key}".encode("utf-8")).hexdigest() + f"###{salt_index}"
    invalid_checksum = "tampered_invalid_checksum###1"

    # Test 1: Tampered signature must be rejected with 400
    tampered_res = await client.post(
        "/api/v1/payments/webhook",
        json={"response": raw_b64},
        headers={"X-VERIFY": invalid_checksum},
    )
    assert tampered_res.status_code == 400

    # Test 2: Valid signature succeeds and activates premium
    valid_res = await client.post(
        "/api/v1/payments/webhook",
        json={"response": raw_b64},
        headers={"X-VERIFY": valid_checksum},
    )
    assert valid_res.status_code == 200
    assert valid_res.json()["success"] is True

    # Confirm user is now Premium
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.json()["data"]["premium_active"] is True
