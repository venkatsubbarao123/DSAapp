"""Base interfaces and data structures for Sandbox code execution."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ExecutionRequest:
    """Request payload for compiling or running untrusted student code."""
    language_id: str
    source_code: str
    stdin: str = ""
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    output_limit_bytes: int = 65536


@dataclass
class CompilationResult:
    """Result of an optional compilation step for compiled languages."""
    success: bool
    compiler_output: str = ""
    exit_code: int = 0
    compilation_time_ms: int = 0


@dataclass
class ExecutionResult:
    """Result of executing the program against a single test case."""
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int = 0
    memory_used_bytes: int = 0
    timed_out: bool = False
    memory_exceeded: bool = False
    output_exceeded: bool = False
    error_message: Optional[str] = None


class BaseSandbox(ABC):
    """Abstract interface for secure code execution sandboxes."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the sandbox runtime (e.g., Docker daemon) is available."""
        pass

    @abstractmethod
    def get_diagnostics(self) -> Dict[str, Any]:
        """Returns diagnostic information about sandbox status, engine, and capabilities."""
        pass

    @abstractmethod
    def compile(self, request: ExecutionRequest) -> CompilationResult:
        """Compiles student code if the language requires compilation."""
        pass

    @abstractmethod
    def run(
        self,
        request: ExecutionRequest,
        workspace_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Executes student code within an isolated, resource-constrained sandbox."""
        pass
