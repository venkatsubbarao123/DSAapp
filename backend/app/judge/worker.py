"""Isolated Judge Worker.

Executes queued judge jobs, applies strict problem resource limits,
evaluates hidden and visible test cases, determines definitive verdicts,
persists execution metrics, and updates user problem progress upon acceptance.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.judge.comparator import compare_outputs
from backend.app.judge.languages import get_language_definition
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox.base import BaseSandbox, ExecutionRequest
from backend.app.judge.sandbox.manager import get_sandbox
from backend.app.models.content import Problem
from backend.app.models.judge import JudgeJob, JudgeJobStatus, SubmissionResult, Verdict
from backend.app.models.progress import (
    ProblemProgressStatus,
    Submission,
    SubmissionStatus,
    UserProblemProgress,
)
from backend.app.services.gamification.streak_service import StreakService
from backend.app.services.gamification.xp_service import XPService, XP_REWARDS

logger = logging.getLogger(__name__)


class JudgeWorker:
    """Worker instance that claims and executes judge jobs."""

    def __init__(
        self, worker_id: str | None = None, sandbox: BaseSandbox | None = None
    ) -> None:
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.sandbox = sandbox or get_sandbox()

    async def execute_job(self, db: AsyncSession, job: JudgeJob) -> bool:
        """Executes a claimed judge job end-to-end."""
        now = datetime.now(timezone.utc)

        # 1. Fetch submission with associated problem and test cases
        stmt = (
            select(Submission)
            .where(Submission.id == job.submission_id)
            .options(selectinload(Submission.problem).selectinload(Problem.test_cases))
        )
        result = await db.execute(stmt)
        submission = result.scalars().first()

        if not submission or not submission.problem:
            job.status = JudgeJobStatus.FAILED
            job.completed_at = now
            job.failure_reason = "Submission or problem not found."
            await db.commit()
            return False

        problem = submission.problem
        test_cases = sorted(problem.test_cases, key=lambda tc: tc.display_order)

        # 2. Check Sandbox availability
        if not self.sandbox.is_available():
            logger.warning(f"Sandbox runtime unavailable for job {job.id}.")
            job.status = JudgeJobStatus.FAILED
            job.completed_at = now
            job.failure_reason = "Sandbox execution environment unavailable (Docker daemon not reachable)."

            # Persist diagnostic result
            sub_res = SubmissionResult(
                submission_id=submission.id,
                verdict=Verdict.SYSTEM_ERROR,
                tests_total=len(test_cases),
                tests_passed=0,
                compiler_output_safe="Execution unavailable: Sandbox container daemon is not reachable in host environment.",
            )
            db.add(sub_res)

            submission.status = SubmissionStatus.SYSTEM_ERROR
            submission.updated_at = now
            await db.commit()
            return False

        # 3. Check Language validity
        lang_def = get_language_definition(submission.language)
        if not lang_def:
            job.status = JudgeJobStatus.FAILED
            job.completed_at = now
            job.failure_reason = f"Unsupported language: {submission.language}"

            sub_res = SubmissionResult(
                submission_id=submission.id,
                verdict=Verdict.SYSTEM_ERROR,
                tests_total=len(test_cases),
                tests_passed=0,
                compiler_output_safe=f"Language '{submission.language}' is not supported.",
            )
            db.add(sub_res)
            submission.status = SubmissionStatus.SYSTEM_ERROR
            submission.updated_at = now
            await db.commit()
            return False

        # 4. Compilation phase (if language requires compilation)
        if lang_def.is_compiled:
            submission.status = SubmissionStatus.COMPILING
            submission.updated_at = now
            await db.commit()

            compile_req = ExecutionRequest(
                language_id=submission.language,
                source_code=submission.source_code,
                memory_limit_mb=problem.memory_limit_mb,
            )
            comp_res = self.sandbox.compile(compile_req)

            if not comp_res.success:
                # Compilation error
                job.status = JudgeJobStatus.COMPLETED
                job.completed_at = datetime.now(timezone.utc)

                sub_res = SubmissionResult(
                    submission_id=submission.id,
                    verdict=Verdict.COMPILATION_ERROR,
                    tests_total=len(test_cases),
                    tests_passed=0,
                    compiler_output_safe=(comp_res.compiler_output or "")[:4096],
                )
                db.add(sub_res)

                submission.status = SubmissionStatus.COMPILATION_ERROR
                submission.updated_at = datetime.now(timezone.utc)
                await db.commit()
                return True

        # 5. Judging phase
        submission.status = SubmissionStatus.JUDGING
        submission.updated_at = datetime.now(timezone.utc)
        await db.commit()

        tests_total = len(test_cases)
        tests_passed = 0
        peak_time_ms = 0
        peak_memory_bytes = 0
        final_verdict = Verdict.ACCEPTED
        runtime_error_output: str | None = None

        time_limit = problem.time_limit_ms or lang_def.default_time_limit_ms
        mem_limit = problem.memory_limit_mb or lang_def.default_memory_limit_mb
        out_limit = problem.output_limit_bytes or 65536
        cmp_mode = problem.comparison_mode or "normalized"

        for tc in test_cases:
            # Heartbeat update
            await JudgeQueue.heartbeat(db, job.id, self.worker_id)

            exec_req = ExecutionRequest(
                language_id=submission.language,
                source_code=submission.source_code,
                stdin=tc.input or "",
                time_limit_ms=time_limit,
                memory_limit_mb=mem_limit,
                output_limit_bytes=out_limit,
            )
            exec_res = self.sandbox.run(exec_req)

            peak_time_ms = max(peak_time_ms, exec_res.execution_time_ms)
            peak_memory_bytes = max(peak_memory_bytes, exec_res.memory_used_bytes)

            if exec_res.timed_out:
                final_verdict = Verdict.TIME_LIMIT_EXCEEDED
                runtime_error_output = "Time Limit Exceeded"
                break

            if exec_res.memory_exceeded:
                final_verdict = Verdict.MEMORY_LIMIT_EXCEEDED
                runtime_error_output = "Memory Limit Exceeded"
                break

            if exec_res.output_exceeded:
                final_verdict = Verdict.OUTPUT_LIMIT_EXCEEDED
                runtime_error_output = "Output Limit Exceeded"
                break

            if exec_res.exit_code != 0:
                final_verdict = Verdict.RUNTIME_ERROR
                err_text = (
                    exec_res.stderr
                    or exec_res.error_message
                    or f"Process exited with code {exec_res.exit_code}"
                )
                runtime_error_output = err_text[:4096]
                break

            # Compare output
            is_match, _diff_msg = compare_outputs(
                exec_res.stdout,
                tc.expected_output,
                mode=cmp_mode,
            )

            if not is_match:
                final_verdict = Verdict.WRONG_ANSWER
                # Never leak full hidden test case output details to untrusted users
                runtime_error_output = "Wrong answer on test case"
                break

            tests_passed += 1

        # 6. Persist SubmissionResult
        sub_res = SubmissionResult(
            submission_id=submission.id,
            verdict=final_verdict,
            tests_total=tests_total,
            tests_passed=tests_passed,
            execution_time_ms=peak_time_ms,
            memory_used_bytes=peak_memory_bytes,
            runtime_output_safe=runtime_error_output,
        )
        db.add(sub_res)

        # 7. Update Submission
        status_map = {
            Verdict.ACCEPTED: SubmissionStatus.ACCEPTED,
            Verdict.WRONG_ANSWER: SubmissionStatus.WRONG_ANSWER,
            Verdict.TIME_LIMIT_EXCEEDED: SubmissionStatus.TIME_LIMIT_EXCEEDED,
            Verdict.MEMORY_LIMIT_EXCEEDED: SubmissionStatus.MEMORY_LIMIT_EXCEEDED,
            Verdict.RUNTIME_ERROR: SubmissionStatus.RUNTIME_ERROR,
            Verdict.COMPILATION_ERROR: SubmissionStatus.COMPILATION_ERROR,
            Verdict.OUTPUT_LIMIT_EXCEEDED: SubmissionStatus.OUTPUT_LIMIT_EXCEEDED,
            Verdict.SYSTEM_ERROR: SubmissionStatus.SYSTEM_ERROR,
        }
        submission.status = status_map.get(final_verdict, SubmissionStatus.SYSTEM_ERROR)
        submission.updated_at = datetime.now(timezone.utc)

        # 8. Update UserProblemProgress (ACCEPTED -> SOLVED invariant)
        progress_stmt = select(UserProblemProgress).where(
            UserProblemProgress.user_id == submission.user_id,
            UserProblemProgress.problem_id == submission.problem_id,
        )
        p_res = await db.execute(progress_stmt)
        progress = p_res.scalars().first()

        now_utc = datetime.now(timezone.utc)
        is_first_solve = False
        if not progress:
            is_first_solve = (final_verdict == Verdict.ACCEPTED)
            progress = UserProblemProgress(
                user_id=submission.user_id,
                problem_id=submission.problem_id,
                status=ProblemProgressStatus.SOLVED
                if final_verdict == Verdict.ACCEPTED
                else ProblemProgressStatus.ATTEMPTED,
                attempts_count=1,
                successful_attempts=1 if final_verdict == Verdict.ACCEPTED else 0,
                first_attempted_at=now_utc,
                last_attempted_at=now_utc,
                solved_at=now_utc if final_verdict == Verdict.ACCEPTED else None,
            )
            db.add(progress)
        else:
            progress.attempts_count += 1
            progress.last_attempted_at = now_utc
            if final_verdict == Verdict.ACCEPTED:
                if progress.status != ProblemProgressStatus.SOLVED:
                    is_first_solve = True
                progress.successful_attempts += 1
                progress.status = ProblemProgressStatus.SOLVED
                if not progress.solved_at:
                    progress.solved_at = now_utc
            elif progress.status != ProblemProgressStatus.SOLVED:
                progress.status = ProblemProgressStatus.ATTEMPTED

        if is_first_solve:
            try:
                async with db.begin_nested():
                    diff_name = str(problem.difficulty).upper() if problem.difficulty else "EASY"
                    reward_key = f"PROBLEM_SOLVE_{diff_name}"
                    amount = XP_REWARDS.get(reward_key, 20)
                    await XPService.record_xp_event(
                        db=db,
                        user_id=submission.user_id,
                        event_type="PROBLEM_SOLVE",
                        source_id=f"problem:{submission.problem_id}",
                        amount=amount,
                        metadata={"difficulty": diff_name, "problem_id": submission.problem_id},
                    )
                    profile = await XPService.get_or_create_profile(db, submission.user_id)
                    profile.total_solves += 1
                    await StreakService.record_activity(
                        db=db, user_id=submission.user_id, activity_type="PROBLEM_SOLVE"
                    )
            except Exception as e:
                logger.warning(f"Could not record gamification for solve: {e}")

        # 9. Mark Job Completed
        job.status = JudgeJobStatus.COMPLETED
        job.completed_at = now_utc
        await db.commit()
        return True
