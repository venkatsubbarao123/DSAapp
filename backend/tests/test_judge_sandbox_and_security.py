"""Tests for Docker sandbox isolation constraints and security diagnostics."""

import pytest
from backend.app.judge.sandbox.docker import DockerSandbox
from backend.app.judge.sandbox.manager import get_sandbox, get_sandbox_diagnostics


def test_docker_sandbox_isolation_spec():
    sandbox = DockerSandbox()
    diag = sandbox.get_diagnostics()

    assert diag["driver"] == "docker"
    assert "isolation" in diag
    iso = diag["isolation"]

    # Security Invariant Verification
    assert iso["network"] == "none", "Sandbox must enforce network=none (strict zero network egress/ingress)"
    assert iso["read_only_rootfs"] is True, "Rootfs must be mounted read-only"
    assert "10001" in iso["user"], "Execution must run under unprivileged user uid 10001"
    assert iso["capabilities_dropped"] == ["ALL"], "All Linux capabilities must be dropped"
    assert iso["no_new_privileges"] is True, "No-new-privileges flag must be set"
    assert iso["pids_limit"] == 64, "PIDs limit must be bounded to prevent fork bombs"


def test_docker_sandbox_safe_availability_probe():
    """Verifies that is_available() safely probes the engine without exceptions or false claims."""
    sandbox = DockerSandbox()
    available = sandbox.is_available()
    assert isinstance(available, bool)

    diag = get_sandbox_diagnostics()
    assert diag["available"] == available
    if not available:
        assert "UNAVAILABLE" in diag["status"]
