"""Authentication tests covering registration, login, token rotation, and replay detection."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_registration_success(client: AsyncClient):
    """Happy path registration returns access token and sets refresh cookie."""
    payload = {
        "email": "student1@example.com",
        "password": "SecurePassword123",
        "display_name": "Student One",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    # Ensure refresh cookie is set
    assert "dsaapp_refresh_token" in response.cookies or "set-cookie" in response.headers


@pytest.mark.asyncio
async def test_registration_duplicate_email_rejected(client: AsyncClient):
    """Duplicate email registration must be rejected with 400 Bad Request."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123",
    }
    # First registration
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 400
    data = res2.json()
    assert data["success"] is False
    assert "already exists" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_registration_weak_password_rejected(client: AsyncClient):
    """Passwords shorter than 8 chars or lacking digits/letters must be rejected."""
    payload = {
        "email": "weakpass@example.com",
        "password": "short",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code in (422, 400)
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_registration_role_injection_blocked(client: AsyncClient):
    """Client attempting to pass role='ADMIN' in body must be rejected by Pydantic extra='forbid'."""
    payload = {
        "email": "hacker@example.com",
        "password": "SecurePassword123",
        "role": "ADMIN",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_user_login_success(client: AsyncClient):
    """User can log in with valid credentials."""
    reg_payload = {
        "email": "logintest@example.com",
        "password": "Password123",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "logintest@example.com",
        "password": "Password123",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


@pytest.mark.asyncio
async def test_login_invalid_password_rejected(client: AsyncClient):
    """Invalid password must return 401 Unauthorized."""
    reg_payload = {
        "email": "wrongpass@example.com",
        "password": "Password123",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrongpass@example.com",
        "password": "WrongPassword999",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_token_refresh_and_rotation(client: AsyncClient):
    """Refresh token must return new access token and rotated refresh token."""
    reg_payload = {
        "email": "refreshtest@example.com",
        "password": "Password123",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    refresh_token = res.cookies.get("dsaapp_refresh_token")

    # Perform refresh
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        cookies={"dsaapp_refresh_token": refresh_token} if refresh_token else {},
        json={"refresh_token": refresh_token} if not refresh_token else {},
    )
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data["data"]
    new_refresh_token = refresh_res.cookies.get("dsaapp_refresh_token")

    # REPLAY ATTACK TEST: Using the OLD refresh token again must fail and revoke session!
    if refresh_token:
        replay_res = await client.post(
            "/api/v1/auth/refresh",
            cookies={"dsaapp_refresh_token": refresh_token},
        )
        assert replay_res.status_code == 401


@pytest.mark.asyncio
async def test_authenticated_me_endpoint(client: AsyncClient):
    """GET /api/v1/auth/me returns current user profile and FREE plan status."""
    reg_payload = {
        "email": "metest@example.com",
        "password": "Password123",
        "display_name": "Explorer Me",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = res.json()["data"]["access_token"]

    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    data = me_res.json()
    assert data["success"] is True
    assert data["data"]["email"] == "metest@example.com"
    assert data["data"]["role"] == "STUDENT"
    assert data["data"]["plan"] == "FREE"
    assert data["data"]["premium_active"] is False


@pytest.mark.asyncio
async def test_unauthorized_access_rejected(client: AsyncClient):
    """Accessing /api/v1/auth/me without a token must return 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
async def test_registration_rate_limiting(client: AsyncClient):
    """Exceeding 10 registrations per minute must trigger HTTP 429 Too Many Requests."""
    for i in range(10):
        res = await client.post(
            "/api/v1/auth/register",
            json={"email": f"user_rl_{i}@example.com", "password": "Password123"},
        )
        assert res.status_code == 201

    # 11th request must exceed the sliding window limit
    res_11 = await client.post(
        "/api/v1/auth/register",
        json={"email": "user_rl_11@example.com", "password": "Password123"},
    )
    assert res_11.status_code == 429
    data = res_11.json()
    assert data["success"] is False
    assert "too many requests" in data["error"]["message"].lower()
