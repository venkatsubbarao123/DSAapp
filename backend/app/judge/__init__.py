"""Phase 5 Online Judge package initialization."""

from backend.app.judge.comparator import ComparisonMode, compare_outputs, normalize_output
from backend.app.judge.languages import (
    LANGUAGE_REGISTRY,
    LanguageDefinition,
    get_language_definition,
    is_language_supported,
)
from backend.app.judge.queue import JudgeQueue
from backend.app.judge.sandbox.base import (
    BaseSandbox,
    CompilationResult,
    ExecutionRequest,
    ExecutionResult,
)
from backend.app.judge.sandbox.docker import DockerSandbox
from backend.app.judge.sandbox.manager import (
    get_sandbox,
    get_sandbox_diagnostics,
    set_sandbox_instance,
)
from backend.app.judge.runner import (
    execute_submission_now,
    run_judge_worker_loop,
    run_sample_test_cases,
)
from backend.app.judge.sandbox.mock import MockSandbox
from backend.app.judge.service import JudgeService
from backend.app.judge.worker import JudgeWorker

__all__ = [
    "ComparisonMode",
    "compare_outputs",
    "normalize_output",
    "LANGUAGE_REGISTRY",
    "LanguageDefinition",
    "get_language_definition",
    "is_language_supported",
    "JudgeQueue",
    "BaseSandbox",
    "CompilationResult",
    "ExecutionRequest",
    "ExecutionResult",
    "DockerSandbox",
    "MockSandbox",
    "get_sandbox",
    "get_sandbox_diagnostics",
    "set_sandbox_instance",
    "JudgeService",
    "JudgeWorker",
    "run_sample_test_cases",
    "execute_submission_now",
    "run_judge_worker_loop",
]
