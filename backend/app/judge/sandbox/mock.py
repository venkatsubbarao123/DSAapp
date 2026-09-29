"""Mock Sandbox for testing the Judge lifecycle and error conditions."""

import time
from typing import Any, Dict, List, Optional

from backend.app.judge.sandbox.base import (
    BaseSandbox,
    CompilationResult,
    ExecutionRequest,
    ExecutionResult,
)


class MockSandbox(BaseSandbox):
    """Mock sandbox for testing judge orchestration, verdicts, and worker states."""

    def __init__(
        self,
        compile_success: bool = True,
        compiler_output: str = "",
        stdout_responses: Optional[List[str]] = None,
        exit_code: int = 0,
        stderr: str = "",
        execution_time_ms: int = 50,
        memory_used_bytes: int = 1024 * 1024 * 16,  # 16 MB
        timed_out: bool = False,
        memory_exceeded: bool = False,
        output_exceeded: bool = False,
        is_available_flag: bool = True,
    ) -> None:
        self.compile_success = compile_success
        self.compiler_output = compiler_output
        self.stdout_responses = stdout_responses or []
        self._response_idx = 0
        self.exit_code = exit_code
        self.stderr = stderr
        self.execution_time_ms = execution_time_ms
        self.memory_used_bytes = memory_used_bytes
        self.timed_out = timed_out
        self.memory_exceeded = memory_exceeded
        self.output_exceeded = output_exceeded
        self.is_available_flag = is_available_flag
        self.executed_requests: List[ExecutionRequest] = []

    def is_available(self) -> bool:
        return self.is_available_flag

    def get_diagnostics(self) -> Dict[str, Any]:
        return {
            "driver": "mock",
            "available": self.is_available_flag,
            "status": "MOCK_TEST_DRIVER",
            "isolation": {"simulated": True},
        }

    def compile(self, request: ExecutionRequest) -> CompilationResult:
        # Detect special trigger strings in code for versatile testing
        if "TRIGGER_COMPILATION_ERROR" in request.source_code:
            return CompilationResult(
                success=False,
                compiler_output="SyntaxError: invalid syntax (mock compile error)",
                exit_code=1,
                compilation_time_ms=10,
            )
        return CompilationResult(
            success=self.compile_success,
            compiler_output=self.compiler_output,
            exit_code=0 if self.compile_success else 1,
            compilation_time_ms=15,
        )

    def run(
        self,
        request: ExecutionRequest,
        workspace_id: Optional[str] = None,
    ) -> ExecutionResult:
        self.executed_requests.append(request)

        # Dynamic triggers based on code keywords
        if "TRIGGER_TLE" in request.source_code:
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Execution timed out.",
                execution_time_ms=request.time_limit_ms + 100,
                timed_out=True,
                error_message="Time Limit Exceeded",
            )
        if "TRIGGER_MLE" in request.source_code:
            return ExecutionResult(
                exit_code=137,
                stdout="",
                stderr="Out of memory.",
                execution_time_ms=30,
                memory_used_bytes=request.memory_limit_mb * 1024 * 1024 + 1024,
                memory_exceeded=True,
                error_message="Memory Limit Exceeded",
            )
        if "TRIGGER_RTE" in request.source_code:
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr="ZeroDivisionError: division by zero",
                execution_time_ms=20,
                error_message="Runtime Error: ZeroDivisionError",
            )
        if "TRIGGER_OLE" in request.source_code:
            return ExecutionResult(
                exit_code=0,
                stdout="A" * (request.output_limit_bytes + 100),
                stderr="",
                execution_time_ms=25,
                output_exceeded=True,
                error_message="Output Limit Exceeded",
            )

        # Normal response handling
        stdout = ""
        if self._response_idx < len(self.stdout_responses):
            stdout = self.stdout_responses[self._response_idx]
            self._response_idx += 1
        elif "TRIGGER_ECHO" in request.source_code:
            # Echo stdin as stdout (useful for test cases where output matches input)
            stdout = request.stdin
        else:
            stdout = "42\n"

        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=stdout,
            stderr=self.stderr,
            execution_time_ms=self.execution_time_ms,
            memory_used_bytes=self.memory_used_bytes,
            timed_out=self.timed_out,
            memory_exceeded=self.memory_exceeded,
            output_exceeded=self.output_exceeded,
        )
