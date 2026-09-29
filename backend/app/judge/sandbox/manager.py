"""Sandbox Driver Factory and Diagnostics Manager.

Strictly manages sandbox lifecycle according to security configuration.
NEVER fabricates container execution.
"""

from typing import Any, Dict, Optional

from backend.app.core.config import settings
from backend.app.judge.sandbox.base import BaseSandbox
from backend.app.judge.sandbox.docker import DockerSandbox
from backend.app.judge.sandbox.mock import MockSandbox

_cached_sandbox: Optional[BaseSandbox] = None


def get_sandbox(override_driver: Optional[str] = None) -> BaseSandbox:
    """Retrieves or instantiates the configured sandbox driver."""
    global _cached_sandbox

    driver = override_driver or settings.JUDGE_SANDBOX_DRIVER

    if driver == "mock":
        return MockSandbox()

    if _cached_sandbox is None or not isinstance(_cached_sandbox, DockerSandbox):
        _cached_sandbox = DockerSandbox()

    return _cached_sandbox


def set_sandbox_instance(sandbox: Optional[BaseSandbox]) -> None:
    """Allows setting an explicit sandbox instance (e.g. for unit and integration test fixtures)."""
    global _cached_sandbox
    _cached_sandbox = sandbox


def get_sandbox_diagnostics() -> Dict[str, Any]:
    """Returns safe diagnostic information regarding the sandbox execution environment."""
    sandbox = get_sandbox()
    return sandbox.get_diagnostics()
