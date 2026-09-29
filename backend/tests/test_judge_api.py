"""Tests for Online Judge API endpoints, IDOR boundaries, and admin controls."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox.mock import MockSandbox
from backend.app.judge.worker import JudgeWorker
from backend.app.models.judge import SubmissionResult, Verdict
from backend.app.models.progress import Submission
from backend.app.models.user import User, UserRole


@pytest.fixture(autouse=True)
async def seed_data():
    async with async_session_factory() as session:
        await seed_development_content(session)


async def register_user(client: AsyncClient, email: str) -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    return login_res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_judge_result_polling_and_idor_protection(client: AsyncClient):
    alice_token = await register_user(client, "alice_judge@example.com")
    bob_token = await register_user(client, "bob_judge@example.com")

    # Alice submits code
    sub_res = await client.post(
        "/api/v1/submissions",
        json={
            "problem_id": "two-sum-seed",
            "language": "python",
            "source_code": "def twoSum(nums, target):\n    return [0, 1]\n",
        },
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert sub_res.status_code == 201
    sub_id = sub_res.json()["data"]["id"]

    # Result not yet ready
    pending_res = await client.get(
        f"/api/v1/submissions/{sub_id}/result",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert pending_res.status_code == 404

    # Run judge worker to complete evaluation
    async with async_session_factory() as session:
        worker = JudgeWorker(worker_id="test-api-worker", sandbox=MockSandbox(stdout_responses=["[0, 1]\n", "[1, 2]\n"]))
        job = await JudgeQueue.claim_next_job(session, worker.worker_id)
        assert job is not None
        await worker.execute_job(session, job)

    # Alice retrieves her result
    res_ready = await client.get(
        f"/api/v1/submissions/{sub_id}/result",
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    assert res_ready.status_code == 200
    res_data = res_ready.json()["data"]
    assert res_data["verdict"] == "ACCEPTED"
    assert res_data["tests_passed"] == res_data["tests_total"]

    # IDOR DEFENSE: Bob tries to fetch Alice's submission result
    bob_attempt = await client.get(
        f"/api/v1/submissions/{sub_id}/result",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert bob_attempt.status_code == 404


@pytest.mark.asyncio
async def test_judge_submission_cancel(client: AsyncClient):
    token = await register_user(client, "cancel_test@example.com")
    sub_res = await client.post(
        "/api/v1/submissions",
        json={
            "problem_id": "two-sum-seed",
            "language": "python",
            "source_code": "print('hello')",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    sub_id = sub_res.json()["data"]["id"]

    # Cancel queued submission
    cancel_res = await client.post(
        f"/api/v1/submissions/{sub_id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["success"] is True


@pytest.mark.asyncio
async def test_admin_judge_health_and_rbac(client: AsyncClient):
    student_token = await register_user(client, "student_rbac@example.com")

    # Student denied access
    res = await client.get(
        "/api/v1/admin/judge/health",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res.status_code == 403

    # Promote user to ADMIN
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "student_rbac@example.com"))).scalar_one()
        user.role = UserRole.ADMIN
        await session.commit()

    # Admin granted access
    admin_res = await client.get(
        "/api/v1/admin/judge/health",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert admin_res.status_code == 200
    health_data = admin_res.json()["data"]
    assert "queue" in health_data
    assert "sandbox" in health_data
    assert health_data["sandbox"]["driver"] == "docker"
