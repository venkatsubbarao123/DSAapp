"""Security tests covering HTTP headers, request correlation, size protection, and error isolation."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    """Responses must contain essential defense-in-depth security headers."""
    response = await client.get("/health")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in response.headers.get("permissions-policy", "")
    assert "frame-ancestors 'none'" in response.headers.get("content-security-policy", "")


@pytest.mark.asyncio
async def test_request_id_preservation(client: AsyncClient):
    """Safe client-supplied request IDs should be preserved."""
    custom_id = "test-req-12345-safe"
    response = await client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.headers.get("x-request-id") == custom_id
    data = response.json()
    assert data["request_id"] == custom_id


@pytest.mark.asyncio
async def test_malicious_request_id_sanitization(client: AsyncClient):
    """Malicious or header-injected request IDs must be replaced with a safe UUID."""
    malicious_id = "malicious<script>alert(1)</script>\r\nInjected-Header: evil"
    response = await client.get("/health", headers={"X-Request-ID": malicious_id})
    assigned_id = response.headers.get("x-request-id")
    assert assigned_id is not None
    assert "<script>" not in assigned_id
    assert "\r" not in assigned_id
    # Should be valid UUID-like safe string
    assert len(assigned_id) >= 32


@pytest.mark.asyncio
async def test_cors_origin_allowlist(client: AsyncClient):
    """Trusted origin receives Access-Control-Allow-Origin; untrusted origin does not."""
    # Trusted origin
    trusted_res = await client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert trusted_res.headers.get("access-control-allow-origin") == "http://localhost:5173"

    # Untrusted origin
    untrusted_res = await client.get("/health", headers={"Origin": "https://malicious-site.com"})
    assert untrusted_res.headers.get("access-control-allow-origin") != "https://malicious-site.com"


@pytest.mark.asyncio
async def test_oversized_payload_rejected(client: AsyncClient):
    """Payloads declaring size greater than MAX_REQUEST_SIZE_BYTES must be rejected with 413."""
    oversized_length = str(10 * 1024 * 1024 + 1000)
    response = await client.post(
        "/api/v1/health",
        headers={"Content-Length": oversized_length},
    )
    assert response.status_code == 413
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_unhandled_error_does_not_leak_traceback(client: AsyncClient):
    """Internal server errors must return generic 500 without leaking stack traces or paths."""
    from backend.app.main import app

    @app.get("/test-internal-error-route")
    async def trigger_error():
        raise RuntimeError("SensitiveDatabaseConnectionFailure: host=10.0.0.12 password=dbsecret")

    response = await client.get("/test-internal-error-route")
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Ensure sensitive runtime exception message and traces are scrubbed
    assert "SensitiveDatabaseConnectionFailure" not in response.text
    assert "password" not in response.text
    assert "Traceback" not in response.text
    assert "request_id" in data["error"]


def test_gitignore_protects_env_and_secrets():
    """Verify that root .gitignore prevents committing .env files and private keys."""
    from pathlib import Path

    gitignore_path = Path(__file__).resolve().parent.parent.parent / ".gitignore"
    assert gitignore_path.exists(), ".gitignore file must exist at repository root"

    content = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in content
    assert "*.key" in content or "*.pem" in content

