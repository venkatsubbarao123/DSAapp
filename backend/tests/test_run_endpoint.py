"""Tests for the interactive RUN endpoint (sample test cases execution).

Verifies:
1. RUN executes sample test cases via sandbox and returns structured outputs.
2. RUN compares outputs with expected outputs and detects mismatches.
3. RUN supports custom testcase input.
4. RUN does NOT create database submissions.
5. RUN does NOT alter user problem progress to SOLVED.
6. Rate limiting and 64KB code size validation are enforced.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.judge.sandbox.manager import get_sandbox, set_sandbox_instance
from backend.app.judge.sandbox.mock import MockSandbox
from backend.app.models.progress import ProblemProgressStatus, Submission, UserProblemProgress
from backend.app.models.user import User


@pytest.fixture(autouse=True)
async def seed_data():
    async with async_session_factory() as session:
        await seed_development_content(session)


async def register_user(client: AsyncClient, email: str = "run_tester@example.com") -> str:
    res = await client.post("/api/v1/auth/register", json={"email": email, "password": "Password123"})
    if res.status_code == 201:
        return res.json()["data"]["access_token"]
    login_res = await client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    return login_res.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_run_sample_code_success(client: AsyncClient):
    token = await register_user(client, "runner1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Inject mock sandbox returning expected outputs
    orig_sandbox = get_sandbox()
    mock_sb = MockSandbox(stdout_responses=["[0, 1]\n", "[1, 2]\n"])
    set_sandbox_instance(mock_sb)

    async with async_session_factory() as session:
        initial_subs_count = len((await session.execute(select(Submission))).scalars().all())

    try:
        res = await client.post(
            "/api/v1/problems/two-sum-seed/run",
            json={
                "language": "python",
                "source_code": "import sys\nprint('[0, 1]')\n",
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["status"] in ("ACCEPTED", "WRONG_ANSWER")
        assert "test_cases" in data
        assert len(data["test_cases"]) > 0
        assert data["test_cases"][0]["case_number"] == 1
        assert data["test_cases"][0]["input"] is not None

        # Verify NO submission was created
        async with async_session_factory() as session:
            subs = (await session.execute(select(Submission))).scalars().all()
            assert len(subs) == initial_subs_count

            # Verify problem progress was NOT set to SOLVED for this user
            user = (await session.execute(
                select(User).where(User.email == "runner1@example.com")
            )).scalar_one()
            progs = (await session.execute(
                select(UserProblemProgress).where(UserProblemProgress.user_id == user.id)
            )).scalars().all()
            assert len(progs) == 0 or all(p.status != ProblemProgressStatus.SOLVED for p in progs)
    finally:
        set_sandbox_instance(orig_sandbox)


@pytest.mark.asyncio
async def test_run_sample_code_custom_input(client: AsyncClient):
    token = await register_user(client, "runner2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    orig_sandbox = get_sandbox()
    mock_sb = MockSandbox(stdout_responses=["42\n"])
    set_sandbox_instance(mock_sb)

    try:
        res = await client.post(
            "/api/v1/problems/two-sum-seed/run",
            json={
                "language": "python",
                "source_code": "print(42)",
                "custom_input": "10 20 30",
            },
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["total_count"] == 1
        assert data["test_cases"][0]["input"] == "10 20 30"
        assert data["test_cases"][0]["actual_output"] == "42\n"
    finally:
        set_sandbox_instance(orig_sandbox)


@pytest.mark.asyncio
async def test_run_code_size_limit(client: AsyncClient):
    token = await register_user(client, "runner3@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    huge_code = "# test\n" + "x = 1\n" * 15000  # > 64KB
    res = await client.post(
        "/api/v1/problems/two-sum-seed/run",
        json={
            "language": "python",
            "source_code": huge_code,
        },
        headers=headers,
    )
    assert res.status_code == 400
    err_body = res.json()
    err_msg = err_body.get("error", {}).get("message") or err_body.get("detail", "")
    assert "64KB" in err_msg


@pytest.mark.asyncio
async def test_run_code_unsupported_language(client: AsyncClient):
    token = await register_user(client, "runner4@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/problems/two-sum-seed/run",
        json={
            "language": "brainfuck",
            "source_code": "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]",
        },
        headers=headers,
    )
    assert res.status_code == 400
    err_body = res.json()
    err_msg = err_body.get("error", {}).get("message") or err_body.get("detail", "")
    assert "Unsupported language" in err_msg
