"""Pytest test configuration and fixtures."""

import os
import sys
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Enforce test environment before loading settings
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_environment_secure_key_for_testing_purposes_only_minimum_64_chars"
os.environ["REDIS_REQUIRED"] = "false"
os.environ["ALLOWED_HOSTS"] = '["localhost", "127.0.0.1", "testserver"]'

from backend.app.main import app
from backend.app.db.init_db import init_db
from backend.app.services.rate_limiter import rate_limiter


@pytest.fixture(autouse=True)
async def setup_test_db():
    """Initializes in-memory database schema and resets rate limits for each test."""
    rate_limiter._local_buckets.clear()
    await init_db()
    yield
    rate_limiter._local_buckets.clear()


@pytest.fixture
async def client():
    """Async test client bound to FastAPI application."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
