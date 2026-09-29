"""Tests for submission creation, non-execution guarantees, idempotency, and source code limits."""

import pytest
from httpx import AsyncClient

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory


@pytest.fixture(autouse=True)
async def seed_data():
    """Seeds verified content before running submission tests."""
    async with async_session_factory() as session:
        await seed_development_content(session)


async def register_and_get_token(client: AsyncClient, email: str = "submit_user@example.com") -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    return res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_create_submission_records_code_without_fake_execution(client: AsyncClient):
    """CRITICAL ANTI-FABRICATION INVARIANT:
    
    Submitting code records the submission with QUEUED_FOR_FUTURE_JUDGE status.
    It DOES NOT execute the code.
    It DOES NOT mark the submission as ACCEPTED or WRONG_ANSWER.
    It advances the problem status to ATTEMPTED, NOT SOLVED.
    """
    token = await register_and_get_token(client, "student_judge@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "problem_id": "two-sum-seed",
        "language": "python",
        "source_code": "def twoSum(nums, target):\n    return [0, 1]\n",
    }
    res = await client.post("/api/v1/submissions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()["data"]

    # Verify NON-EXECUTED status
    assert data["status"] == "QUEUED_FOR_FUTURE_JUDGE"
    assert "QUEUED" in data["status"] or "NOT_EXECUTED" in data["status"]
    assert data["status"] != "ACCEPTED"
    assert data["status"] != "WRONG_ANSWER"
    assert "Phase 7" in data["execution_notice"]

    # Check problem progress: MUST be ATTEMPTED, NOT SOLVED
    prog_res = await client.get("/api/v1/progress/problems/two-sum-seed", headers=headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()["data"]
    assert prog_data["status"] == "ATTEMPTED"
    assert prog_data["status"] != "SOLVED"
    assert prog_data["attempts_count"] == 1


@pytest.mark.asyncio
async def test_submission_idempotency_key_prevents_duplicate_records(client: AsyncClient):
    """Submitting with identical Idempotency-Key returns existing submission."""
    token = await register_and_get_token(client, "idempotent_user@example.com")
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "client-uuid-sub-attempt-1",
    }

    payload = {
        "problem_id": "two-sum-seed",
        "language": "python",
        "source_code": "def solution(): pass",
    }

    # First request
    res1 = await client.post("/api/v1/submissions", json=payload, headers=headers)
    assert res1.status_code == 201
    sub_id1 = res1.json()["data"]["id"]

    # Second request with same idempotency key
    res2 = await client.post("/api/v1/submissions", json=payload, headers=headers)
    assert res2.status_code == 201
    sub_id2 = res2.json()["data"]["id"]

    assert sub_id1 == sub_id2


@pytest.mark.asyncio
async def test_submission_source_code_size_limit_enforced(client: AsyncClient):
    """Source code exceeding 64KB is rejected with HTTP 422."""
    token = await register_and_get_token(client, "bloat_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 65KB payload
    oversized_code = "x = 1\n" * 15000
    assert len(oversized_code.encode("utf-8")) > 64 * 1024

    payload = {
        "problem_id": "two-sum-seed",
        "language": "python",
        "source_code": oversized_code,
    }
    res = await client.post("/api/v1/submissions", json=payload, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_submission_unsupported_language_rejected(client: AsyncClient):
    """Submitting unsupported language is rejected with HTTP 422."""
    token = await register_and_get_token(client, "lang_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "problem_id": "two-sum-seed",
        "language": "brainfuck",
        "source_code": "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.",
    }
    res = await client.post("/api/v1/submissions", json=payload, headers=headers)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_submission_list_omits_source_code_and_detail_includes_it(client: AsyncClient):
    """List endpoint excludes source_code for performance; detail endpoint provides it."""
    token = await register_and_get_token(client, "history_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    secret_code = "def my_private_algorithm(): return 42"
    payload = {
        "problem_id": "two-sum-seed",
        "language": "python",
        "source_code": secret_code,
    }
    create_res = await client.post("/api/v1/submissions", json=payload, headers=headers)
    sub_id = create_res.json()["data"]["id"]

    # 1. List submissions
    list_res = await client.get("/api/v1/submissions", headers=headers)
    assert list_res.status_code == 200
    items = list_res.json()["data"]["items"]
    assert len(items) == 1
    assert "source_code" not in items[0]  # Excluded from summary

    # 2. Detail submission
    detail_res = await client.get(f"/api/v1/submissions/{sub_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["source_code"] == secret_code
