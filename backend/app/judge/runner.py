"""Judge runner and sample execution engine.

Provides:
1. Isolated sample-case RUN execution (non-persistent, no progress mutation).
2. Background judge worker polling loop for continuous evaluation.
3. Synchronous/immediate evaluation helper for fast feedback.
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.judge.comparator import compare_outputs
from backend.app.judge.languages import get_language_definition
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox.base import ExecutionRequest
from backend.app.judge.sandbox.manager import get_sandbox
from backend.app.judge.worker import JudgeWorker
from backend.app.models.content import ContentStatus, Problem, TestCase
from backend.app.models.judge import JudgeJob, JudgeJobStatus
from backend.app.schemas.judge import RunCodeResponse, TestCaseRunResult

logger = logging.getLogger(__name__)


async def run_sample_test_cases(
    db: AsyncSession,
    problem_id_or_slug: str,
    language: str,
    source_code: str,
    custom_input: Optional[str] = None,
) -> RunCodeResponse:
    """Executes code against public/sample test cases without mutating submission history.
    
    CRITICAL NON-GOALS & SECURITY INVARIANTS:
    1. NEVER writes to the `submissions` table or alters `UserProblemProgress`.
    2. NEVER executes against hidden test cases.
    3. Strictly enforces 64KB source code cap and language allowlist.
    4. Executes exclusively inside zero-network, resource-isolated sandbox.
    """
    # 1. Enforce 64KB max code
    if len(source_code.encode("utf-8")) > 65536:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source code exceeds maximum allowed size of 64KB.",
        )

    # 2. Validate language
    lang_def = get_language_definition(language)
    if not lang_def:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language '{language}'.",
        )

    # 3. Fetch problem and test cases
    stmt = (
        select(Problem)
        .where(
            or_(Problem.id == problem_id_or_slug, Problem.slug == problem_id_or_slug),
            Problem.status == ContentStatus.PUBLISHED,
        )
        .options(selectinload(Problem.test_cases))
    )
    res = await db.execute(stmt)
    problem = res.scalars().first()

    if not problem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found or unavailable.",
        )

    # 4. Check sandbox availability
    sandbox = get_sandbox()
    if not sandbox.is_available():
        return RunCodeResponse(
            status="SYSTEM_ERROR",
            all_passed=False,
            passed_count=0,
            total_count=0,
            peak_runtime_ms=0,
            peak_memory_bytes=0,
            compiler_output="Execution sandbox unavailable (Docker daemon is not reachable).",
            test_cases=[],
        )

    # 5. Compilation phase (if language requires compilation)
    time_limit = problem.time_limit_ms or lang_def.default_time_limit_ms
    mem_limit = problem.memory_limit_mb or lang_def.default_memory_limit_mb

    if lang_def.is_compiled and lang_def.compile_command:
        compile_req = ExecutionRequest(
            language_id=language,
            source_code=source_code,
            memory_limit_mb=mem_limit,
        )
        comp_res = sandbox.compile(compile_req)
        if not comp_res.success:
            return RunCodeResponse(
                status="COMPILATION_ERROR",
                all_passed=False,
                passed_count=0,
                total_count=0,
                peak_runtime_ms=comp_res.compilation_time_ms,
                peak_memory_bytes=0,
                compiler_output=(comp_res.compiler_output or "")[:4096],
                test_cases=[],
            )

    # 6. Prepare test cases to run
    if custom_input is not None:
        exec_req = ExecutionRequest(
            language_id=language,
            source_code=source_code,
            stdin=custom_input,
            time_limit_ms=time_limit,
            memory_limit_mb=mem_limit,
        )
        exec_res = sandbox.run(exec_req)

        passed = (exec_res.exit_code == 0 and not exec_res.timed_out and not exec_res.memory_exceeded)
        case_status = (
            "ACCEPTED"
            if passed
            else (
                "TIME_LIMIT_EXCEEDED"
                if exec_res.timed_out
                else ("MEMORY_LIMIT_EXCEEDED" if exec_res.memory_exceeded else "RUNTIME_ERROR")
            )
        )

        case_result = TestCaseRunResult(
            case_number=1,
            input=custom_input,
            expected_output=None,
            actual_output=exec_res.stdout,
            stderr=exec_res.stderr or exec_res.error_message,
            passed=passed,
            execution_time_ms=exec_res.execution_time_ms,
            status=case_status,
        )

        return RunCodeResponse(
            status=case_status,
            all_passed=passed,
            passed_count=1 if passed else 0,
            total_count=1,
            peak_runtime_ms=exec_res.execution_time_ms,
            peak_memory_bytes=exec_res.memory_used_bytes,
            compiler_output=None,
            test_cases=[case_result],
        )

    # Extract sample test cases (fallback to first 2 test cases if none explicitly marked)
    all_cases = sorted(problem.test_cases, key=lambda tc: tc.display_order)
    sample_cases = [tc for tc in all_cases if tc.is_sample]
    if not sample_cases:
        sample_cases = all_cases[:2]

    if not sample_cases:
        return RunCodeResponse(
            status="SYSTEM_ERROR",
            all_passed=False,
            passed_count=0,
            total_count=0,
            peak_runtime_ms=0,
            peak_memory_bytes=0,
            compiler_output="No sample test cases configured for this problem.",
            test_cases=[],
        )

    test_case_results = []
    peak_time_ms = 0
    peak_mem_bytes = 0
    cmp_mode = problem.comparison_mode or "normalized"

    for idx, tc in enumerate(sample_cases):
        exec_req = ExecutionRequest(
            language_id=language,
            source_code=source_code,
            stdin=tc.input or "",
            time_limit_ms=time_limit,
            memory_limit_mb=mem_limit,
        )
        exec_res = sandbox.run(exec_req)

        peak_time_ms = max(peak_time_ms, exec_res.execution_time_ms)
        peak_mem_bytes = max(peak_mem_bytes, exec_res.memory_used_bytes)

        if exec_res.timed_out:
            case_status = "TIME_LIMIT_EXCEEDED"
            passed = False
        elif exec_res.memory_exceeded:
            case_status = "MEMORY_LIMIT_EXCEEDED"
            passed = False
        elif exec_res.exit_code != 0:
            case_status = "RUNTIME_ERROR"
            passed = False
        else:
            is_match, _ = compare_outputs(exec_res.stdout, tc.expected_output, mode=cmp_mode)
            case_status = "ACCEPTED" if is_match else "WRONG_ANSWER"
            passed = is_match

        test_case_results.append(
            TestCaseRunResult(
                case_number=idx + 1,
                input=tc.input or "",
                expected_output=tc.expected_output or "",
                actual_output=exec_res.stdout or "",
                stderr=(exec_res.stderr or exec_res.error_message or "")[:2048] if not passed else None,
                passed=passed,
                execution_time_ms=exec_res.execution_time_ms,
                status=case_status,
            )
        )

    all_passed = all(c.passed for c in test_case_results)
    passed_count = sum(1 for c in test_case_results if c.passed)
    total_count = len(test_case_results)

    if all_passed:
        overall_status = "ACCEPTED"
    elif any(c.status == "TIME_LIMIT_EXCEEDED" for c in test_case_results):
        overall_status = "TIME_LIMIT_EXCEEDED"
    elif any(c.status == "RUNTIME_ERROR" for c in test_case_results):
        overall_status = "RUNTIME_ERROR"
    else:
        overall_status = "WRONG_ANSWER"

    return RunCodeResponse(
        status=overall_status,
        all_passed=all_passed,
        passed_count=passed_count,
        total_count=total_count,
        peak_runtime_ms=peak_time_ms,
        peak_memory_bytes=peak_mem_bytes,
        compiler_output=None,
        test_cases=test_case_results,
    )


async def execute_submission_now(submission_id: str) -> bool:
    """Executes a queued judge job immediately using an isolated session."""
    from backend.app.db.session import async_session_factory
    async with async_session_factory() as session:
        stmt = select(JudgeJob).where(JudgeJob.submission_id == submission_id)
        res = await session.execute(stmt)
        job = res.scalars().first()
        if job and job.status in (JudgeJobStatus.QUEUED, JudgeJobStatus.RETRY_PENDING):
            worker = JudgeWorker()
            job.status = JudgeJobStatus.CLAIMED
            job.worker_id = worker.worker_id
            job.started_at = datetime.now(timezone.utc)
            await session.commit()
            return await worker.execute_job(session, job)
        return False


async def run_judge_worker_loop(interval_seconds: float = 0.5) -> None:
    """Continuously claims and evaluates queued judge jobs in the background."""
    from backend.app.db.session import async_session_factory
    worker = JudgeWorker()
    logger.info(f"Online Judge background worker loop initialized (worker={worker.worker_id}).")

    while True:
        try:
            async with async_session_factory() as session:
                job = await JudgeQueue.claim_next_job(session, worker.worker_id)
                if job:
                    logger.info(f"Worker {worker.worker_id} processing job {job.id} (submission={job.submission_id})")
                    await worker.execute_job(session, job)
                    continue
        except asyncio.CancelledError:
            logger.info("Judge worker background loop shutting down gracefully.")
            break
        except Exception as exc:
            logger.debug(f"Judge worker loop idle/exception: {exc}")
        await asyncio.sleep(interval_seconds)
