"""Tests for health, liveness, and readiness endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health_endpoint(client: AsyncClient):
    """GET /health must return 200 with structured health metrics."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "dsaapp-api"
    assert data["data"]["database"] == "connected"
    assert "request_id" in data
    assert response.headers.get("x-request-id") is not None


@pytest.mark.asyncio
async def test_root_liveness_endpoint(client: AsyncClient):
    """GET /liveness must return 200 with process status alive."""
    response = await client.get("/liveness")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "alive"
    assert data["data"]["service"] == "dsaapp-api"
    assert response.headers.get("x-request-id") is not None


@pytest.mark.asyncio
async def test_root_readiness_endpoint(client: AsyncClient):
    """GET /readiness must return 200 when database is ready."""
    response = await client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "ready"
    assert data["data"]["database"] == "connected"
    assert response.headers.get("x-request-id") is not None


@pytest.mark.asyncio
async def test_api_v1_health_endpoint(client: AsyncClient):
    """GET /api/v1/health must return 200 with structured health metrics."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["status"] == "healthy"
    assert data["data"]["service"] == "dsaapp-api"
    assert data["data"]["database"] == "connected"
    assert "request_id" in data
    assert response.headers.get("x-request-id") is not None


@pytest.mark.asyncio
async def test_api_v1_live_and_ready_endpoints(client: AsyncClient):
    """GET /api/v1/health/live and /ready must return 200."""
    live_resp = await client.get("/api/v1/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["data"]["status"] == "alive"

    ready_resp = await client.get("/api/v1/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["data"]["status"] == "ready"


@pytest.mark.asyncio
async def test_nonexistent_endpoint_returns_standard_error(client: AsyncClient):
    """Accessing an undefined endpoint must return standard error envelope."""
    response = await client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]
    assert response.headers.get("x-request-id") is not None
