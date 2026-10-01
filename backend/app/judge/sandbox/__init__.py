"""Sandbox package initialization."""

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
from backend.app.judge.sandbox.mock import MockSandbox

__all__ = [
    "BaseSandbox",
    "CompilationResult",
    "DockerSandbox",
    "ExecutionRequest",
    "ExecutionResult",
    "MockSandbox",
    "get_sandbox",
    "get_sandbox_diagnostics",
    "set_sandbox_instance",
]
