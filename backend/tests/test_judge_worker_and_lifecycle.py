"""Tests for JudgeWorker execution lifecycle, verdicts, and progress synchronization."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.seed_data import seed_development_content
from backend.app.db.session import async_session_factory
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox.mock import MockSandbox
from backend.app.judge.worker import JudgeWorker
from backend.app.models.content import Problem
from backend.app.models.judge import JudgeJob, JudgeJobStatus, SubmissionResult, Verdict
from backend.app.models.progress import (
    ProblemProgressStatus,
    Submission,
    SubmissionStatus,
    UserProblemProgress,
)
from backend.app.models.user import User


@pytest.fixture(autouse=True)
async def setup_seed_and_user():
    async with async_session_factory() as session:
        await seed_development_content(session)
        existing_user = (await session.execute(select(User).where(User.email == "judge_worker_test@example.com"))).scalar_one_or_none()
        if not existing_user:
            user = User(email="judge_worker_test@example.com", hashed_password="hashed_pwd")
            session.add(user)
            await session.commit()


@pytest.mark.asyncio
async def test_judge_worker_accepted_verdict_updates_progress_to_solved():
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "judge_worker_test@example.com"))).scalar_one()
        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        # Create submission
        sub = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="python",
            source_code="def twoSum(nums, target):\n    TRIGGER_ECHO\n",
            status=SubmissionStatus.QUEUED,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        # Enqueue job
        job = await JudgeQueue.enqueue(session, sub.id)
        assert job.status == JudgeJobStatus.QUEUED

        # Claim job with worker
        worker_sandbox = MockSandbox(stdout_responses=["[0, 1]\n", "[1, 2]\n"])
        worker = JudgeWorker(worker_id="test-worker-1", sandbox=worker_sandbox)

        claimed = await JudgeQueue.claim_next_job(session, worker.worker_id)
        assert claimed is not None
        assert claimed.id == job.id

        # Execute
        success = await worker.execute_job(session, claimed)
        assert success is True

        # Verify job and submission status
        await session.refresh(claimed)
        await session.refresh(sub)
        assert claimed.status == JudgeJobStatus.COMPLETED
        assert sub.status == SubmissionStatus.ACCEPTED

        # Verify SubmissionResult
        res_stmt = select(SubmissionResult).where(SubmissionResult.submission_id == sub.id)
        res = (await session.execute(res_stmt)).scalar_one()
        assert res.verdict == Verdict.ACCEPTED
        assert res.tests_passed == res.tests_total

        # CRITICAL PROGRESS INVARIANT: ACCEPTED submission marks problem SOLVED
        prog_stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.problem_id == prob.id,
        )
        prog = (await session.execute(prog_stmt)).scalar_one()
        assert prog.status == ProblemProgressStatus.SOLVED
        assert prog.solved_at is not None
        assert prog.successful_attempts == 1


@pytest.mark.asyncio
async def test_judge_worker_wrong_answer_keeps_status_attempted():
    async with async_session_factory() as session:
        user = User(email="wa_worker_test@example.com", hashed_password="pwd")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        sub = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="python",
            source_code="return [999, 999]\n",
            status=SubmissionStatus.QUEUED,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        job = await JudgeQueue.enqueue(session, sub.id)
        worker_sandbox = MockSandbox(stdout_responses=["[999, 999]\n"])
        worker = JudgeWorker(worker_id="test-worker-wa", sandbox=worker_sandbox)

        claimed = await JudgeQueue.claim_next_job(session, worker.worker_id)
        await worker.execute_job(session, claimed)

        await session.refresh(sub)
        assert sub.status == SubmissionStatus.WRONG_ANSWER

        prog = (await session.execute(select(UserProblemProgress).where(
            UserProblemProgress.user_id == user.id,
            UserProblemProgress.problem_id == prob.id,
        ))).scalar_one()
        # MUST remain ATTEMPTED, NOT SOLVED
        assert prog.status == ProblemProgressStatus.ATTEMPTED
        assert prog.successful_attempts == 0


@pytest.mark.asyncio
async def test_judge_worker_compilation_error_flow():
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "judge_worker_test@example.com"))).scalar_one()
        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        sub = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="cpp",
            source_code="int main() { TRIGGER_COMPILATION_ERROR }",
            status=SubmissionStatus.QUEUED,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)

        job = await JudgeQueue.enqueue(session, sub.id)
        worker = JudgeWorker(worker_id="test-worker-ce", sandbox=MockSandbox())

        claimed = await JudgeQueue.claim_next_job(session, worker.worker_id)
        await worker.execute_job(session, claimed)

        await session.refresh(sub)
        assert sub.status == SubmissionStatus.COMPILATION_ERROR

        res = (await session.execute(select(SubmissionResult).where(SubmissionResult.submission_id == sub.id))).scalar_one()
        assert res.verdict == Verdict.COMPILATION_ERROR
        assert "SyntaxError" in res.compiler_output_safe


@pytest.mark.asyncio
async def test_judge_worker_tle_verdict():
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "judge_worker_test@example.com"))).scalar_one()
        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        sub = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="python",
            source_code="while True: pass # TRIGGER_TLE",
            status=SubmissionStatus.QUEUED,
        )
        session.add(sub)
        await session.commit()

        job = await JudgeQueue.enqueue(session, sub.id)
        worker = JudgeWorker(worker_id="test-worker-tle", sandbox=MockSandbox())

        claimed = await JudgeQueue.claim_next_job(session, worker.worker_id)
        await worker.execute_job(session, claimed)

        await session.refresh(sub)
        assert sub.status == SubmissionStatus.TIME_LIMIT_EXCEEDED


@pytest.mark.asyncio
async def test_judge_worker_mle_verdict():
    async with async_session_factory() as session:
        user = (await session.execute(select(User).where(User.email == "judge_worker_test@example.com"))).scalar_one()
        prob = (await session.execute(select(Problem).where(Problem.slug == "two-sum-seed"))).scalar_one()

        sub = Submission(
            user_id=user.id,
            problem_id=prob.id,
            language="python",
            source_code="TRIGGER_MLE",
            status=SubmissionStatus.QUEUED,
        )
        session.add(sub)
        await session.commit()

        job = await JudgeQueue.enqueue(session, sub.id)
        worker = JudgeWorker(worker_id="test-worker-mle", sandbox=MockSandbox())

        claimed = await JudgeQueue.claim_next_job(session, worker.worker_id)
        await worker.execute_job(session, claimed)

        await session.refresh(sub)
        assert sub.status == SubmissionStatus.MEMORY_LIMIT_EXCEEDED
