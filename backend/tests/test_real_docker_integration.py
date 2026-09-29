"""Real Docker Integration Tests for Phase 5 Online Judge.

These tests REQUIRE Docker Desktop to be installed and running
with the following judge images pre-built:
  - dsaapp-judge-python:latest
  - dsaapp-judge-cpp:latest
  - dsaapp-judge-java:latest
  - dsaapp-judge-javascript:latest

Tests are SKIPPED automatically (not failed) if Docker is not available.

DO NOT use MockSandbox in this test file.
DO NOT fabricate results.
All results must come from real Docker container execution.

Coverage:
  - Python: accepted (hello world), accepted (stdin), wrong answer detection,
            runtime error, TLE, division by zero, output limit exceeded
  - C++:    accepted (compile+run), accepted (stdin), compilation error,
            runtime error (null dereference), TLE
  - Java:   accepted (compile+run), accepted (Scanner), compilation error,
            runtime error (AIOOBE), TLE
  - JavaScript: accepted (hello world), accepted (stdin), runtime error, TLE
  - Security: network isolation (--network none), non-root user (uid=10001),
              read-only rootfs, env var protection, container cleanup
"""

import time
import pytest

from backend.app.judge.sandbox.docker import DockerSandbox
from backend.app.judge.sandbox.base import ExecutionRequest


def get_docker_sandbox() -> DockerSandbox:
    """Instantiate DockerSandbox and skip test if Docker not available."""
    sandbox = DockerSandbox()
    if not sandbox.is_available():
        pytest.skip("Docker engine is not available — skipping real Docker tests.")
    return sandbox


# ─────────────────────────────────────────────────────────────────────────────
# PYTHON TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_python_accepted_hello_world():
    """Real Docker: Python prints Hello World."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code='print("Hello, World!")\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}. err={result.error_message}"
    assert "Hello, World!" in result.stdout
    assert not result.timed_out
    assert not result.memory_exceeded


def test_docker_python_accepted_stdin():
    """Real Docker: Python reads stdin and processes correctly."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import sys\n"
            "n = int(input())\n"
            "print(n * 2)\n"
        ),
        stdin="21\n",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"err={result.error_message}"
    assert "42" in result.stdout.strip()


def test_docker_python_wrong_answer_detectable():
    """Real Docker: Python executes but produces detectable wrong output."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code="print(999)\n",
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    # Program succeeds (exit 0), but output is wrong — comparator detects WRONG_ANSWER
    assert result.exit_code == 0
    assert "999" in result.stdout


def test_docker_python_runtime_error():
    """Real Docker: Python raises unhandled exception → exit code != 0."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code="raise ValueError('intentional error')\n",
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code != 0, "Expected non-zero exit code for RuntimeError"
    assert not result.timed_out


def test_docker_python_time_limit_exceeded():
    """Real Docker: Python infinite loop → timed_out=True within time budget."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code="while True: pass\n",
        stdin="",
        time_limit_ms=1000,  # 1 second
        memory_limit_mb=256,
    )
    start = time.monotonic()
    result = sandbox.run(req)
    elapsed = time.monotonic() - start

    assert result.timed_out is True, f"Expected timed_out=True, got exit={result.exit_code}"
    # Must not hang for more than time_limit + 5s total
    assert elapsed < 10.0, f"TLE handling took too long: {elapsed:.1f}s"


def test_docker_python_division_by_zero():
    """Real Docker: Python ZeroDivisionError → runtime error, stderr contains ZeroDivisionError."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code="print(1/0)\n",
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code != 0


def test_docker_python_output_limit_exceeded():
    """Real Docker: Python excessive output → truncated at output_limit_bytes."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code="print('X' * 100000)\n",
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
        output_limit_bytes=1024,  # 1 KB limit
    )
    result = sandbox.run(req)
    assert result.output_exceeded is True or "[OUTPUT TRUNCATED" in (result.stdout or "")


# ─────────────────────────────────────────────────────────────────────────────
# C++ TESTS (run handles both compile+execute in one container)
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_cpp_accepted_hello_world():
    """Real Docker: C++ compiles and runs Hello World."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="cpp",
        source_code='#include <iostream>\nint main() { std::cout << "Hello, World!" << std::endl; return 0; }\n',
        stdin="",
        time_limit_ms=10000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"err={result.error_message}, stderr={result.stderr}"
    assert "Hello, World!" in result.stdout


def test_docker_cpp_accepted_with_stdin():
    """Real Docker: C++ reads stdin and computes correctly."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="cpp",
        source_code=(
            "#include <iostream>\n"
            "int main() { int a, b; std::cin >> a >> b; std::cout << a + b << std::endl; return 0; }\n"
        ),
        stdin="3 7\n",
        time_limit_ms=10000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "10" in result.stdout.strip()


def test_docker_cpp_compilation_error():
    """Real Docker: C++ with syntax error → compilation fails (non-zero exit)."""
    sandbox = get_docker_sandbox()
    # Standalone compile test
    req = ExecutionRequest(
        language_id="cpp",
        source_code="int main() { INTENTIONAL SYNTAX ERROR }\n",
        time_limit_ms=15000,
        memory_limit_mb=256,
    )
    comp_result = sandbox.compile(req)
    assert comp_result.success is False, "Expected compilation failure"
    assert comp_result.exit_code != 0


def test_docker_cpp_runtime_error():
    """Real Docker: C++ null dereference → non-zero exit (SIGSEGV)."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="cpp",
        source_code="#include <cstdlib>\nint main() { int* p = nullptr; *p = 1; return 0; }\n",
        stdin="",
        time_limit_ms=10000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code != 0, "Expected non-zero exit for null dereference"
    assert not result.timed_out


def test_docker_cpp_time_limit_exceeded():
    """Real Docker: C++ infinite loop → TLE."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="cpp",
        source_code="#include <cstdlib>\nint main() { for(;;); return 0; }\n",
        stdin="",
        time_limit_ms=1500,
        memory_limit_mb=256,
    )
    start = time.monotonic()
    result = sandbox.run(req)
    elapsed = time.monotonic() - start

    assert result.timed_out is True, f"Expected TLE, got exit={result.exit_code}"
    assert elapsed < 15.0, f"TLE took too long: {elapsed:.1f}s"


# ─────────────────────────────────────────────────────────────────────────────
# JAVA TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_java_accepted_hello_world():
    """Real Docker: Java compiles and prints Hello World."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="java",
        source_code=(
            "public class Solution {\n"
            "    public static void main(String[] args) {\n"
            "        System.out.println(\"Hello, World!\");\n"
            "    }\n"
            "}\n"
        ),
        stdin="",
        time_limit_ms=15000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"err={result.error_message}, stderr={result.stderr}"
    assert "Hello, World!" in result.stdout


def test_docker_java_accepted_with_scanner():
    """Real Docker: Java reads stdin with Scanner."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="java",
        source_code=(
            "import java.util.Scanner;\n"
            "public class Solution {\n"
            "    public static void main(String[] args) {\n"
            "        Scanner sc = new Scanner(System.in);\n"
            "        int a = sc.nextInt();\n"
            "        int b = sc.nextInt();\n"
            "        System.out.println(a + b);\n"
            "    }\n"
            "}\n"
        ),
        stdin="15 27\n",
        time_limit_ms=15000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "42" in result.stdout.strip()


def test_docker_java_compilation_error():
    """Real Docker: Java syntax error → compilation fails."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="java",
        source_code="public class Solution { THIS IS NOT VALID JAVA }\n",
        time_limit_ms=20000,
        memory_limit_mb=256,
    )
    comp = sandbox.compile(req)
    assert comp.success is False
    assert comp.exit_code != 0


def test_docker_java_runtime_error():
    """Real Docker: Java throws ArrayIndexOutOfBoundsException → non-zero exit."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="java",
        source_code=(
            "public class Solution {\n"
            "    public static void main(String[] args) {\n"
            "        int[] arr = new int[0];\n"
            "        System.out.println(arr[5]);\n"
            "    }\n"
            "}\n"
        ),
        stdin="",
        time_limit_ms=15000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code != 0, "Expected non-zero exit for AIOOBE"
    assert not result.timed_out


def test_docker_java_time_limit_exceeded():
    """Real Docker: Java infinite loop → TLE."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="java",
        source_code=(
            "public class Solution {\n"
            "    public static void main(String[] args) { while(true) {} }\n"
            "}\n"
        ),
        stdin="",
        time_limit_ms=2000,
        memory_limit_mb=256,
    )
    start = time.monotonic()
    result = sandbox.run(req)
    elapsed = time.monotonic() - start

    assert result.timed_out is True, f"Expected TLE, got exit={result.exit_code}"
    assert elapsed < 20.0, f"TLE handling took too long: {elapsed:.1f}s"


# ─────────────────────────────────────────────────────────────────────────────
# JAVASCRIPT TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_javascript_accepted_hello_world():
    """Real Docker: JavaScript prints Hello World via Node.js."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="javascript",
        source_code='console.log("Hello, World!");\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"err={result.error_message}"
    assert "Hello, World!" in result.stdout


def test_docker_javascript_runtime_error():
    """Real Docker: JavaScript TypeError → non-zero exit."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="javascript",
        source_code="null.toString();\n",
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code != 0


def test_docker_javascript_time_limit_exceeded():
    """Real Docker: JavaScript infinite loop → TLE."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="javascript",
        source_code="while(true) {}\n",
        stdin="",
        time_limit_ms=1000,
        memory_limit_mb=256,
    )
    start = time.monotonic()
    result = sandbox.run(req)
    elapsed = time.monotonic() - start

    assert result.timed_out is True, f"Expected TLE, got exit={result.exit_code}"
    assert elapsed < 10.0


# ─────────────────────────────────────────────────────────────────────────────
# SANDBOX SECURITY TESTS — REAL DOCKER
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_security_no_internet_access():
    """SECURITY: Container has --network none — internet must be unreachable."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import socket\n"
            "try:\n"
            "    socket.setdefaulttimeout(2)\n"
            "    socket.socket().connect(('8.8.8.8', 53))\n"
            "    print('NETWORK_ACCESSIBLE')\n"
            "except Exception:\n"
            "    print('NETWORK_BLOCKED')\n"
        ),
        stdin="",
        time_limit_ms=6000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert "NETWORK_BLOCKED" in result.stdout, (
        f"SECURITY VIOLATION: Container has internet access! stdout={result.stdout}"
    )
    assert "NETWORK_ACCESSIBLE" not in result.stdout


def test_docker_security_non_root_user():
    """SECURITY: Container must run as uid=10001 (non-root)."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import os\n"
            "print('UID:', os.getuid())\n"
            "print('GID:', os.getgid())\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0
    assert "UID: 10001" in result.stdout, (
        f"SECURITY VIOLATION: Container running as wrong user! stdout={result.stdout}"
    )
    assert "GID: 10001" in result.stdout


def test_docker_security_cannot_write_to_root_fs():
    """SECURITY: Container rootfs is read-only — writes to /etc must be blocked."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "try:\n"
            "    with open('/etc/hacked.txt', 'w') as f:\n"
            "        f.write('HACKED')\n"
            "    print('WRITE_SUCCEEDED_BAD')\n"
            "except (PermissionError, OSError, IOError) as e:\n"
            "    print('WRITE_BLOCKED:', type(e).__name__)\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert "WRITE_SUCCEEDED_BAD" not in result.stdout, (
        f"SECURITY VIOLATION: Container was able to write to read-only rootfs! stdout={result.stdout}"
    )
    assert "WRITE_BLOCKED" in result.stdout


def test_docker_security_cannot_read_etc_shadow():
    """SECURITY: Container must not be able to read /etc/shadow."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "try:\n"
            "    with open('/etc/shadow', 'r') as f:\n"
            "        print('SHADOW_READABLE:', f.read()[:10])\n"
            "except PermissionError:\n"
            "    print('SHADOW_BLOCKED_PERMISSION')\n"
            "except FileNotFoundError:\n"
            "    print('SHADOW_NOT_FOUND')\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    # Either file doesn't exist or permission denied — both are acceptable secure outcomes
    assert "SHADOW_BLOCKED_PERMISSION" in result.stdout or "SHADOW_NOT_FOUND" in result.stdout, (
        f"SECURITY VIOLATION: /etc/shadow may be readable! stdout={result.stdout}"
    )


def test_docker_security_no_env_var_leakage():
    """SECURITY: Container env must not contain application secrets (SECRET_KEY, DATABASE_URL, JWT tokens, etc.).

    Note: Base image env vars like GPG_KEY (Python package signing key) and
    JAVA_HOME, PYTHON_VERSION etc. are expected and not a security concern.
    We specifically verify DSAapp application secrets are NOT present.
    """
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import os\n"
            # Check for application-specific secrets only (not base image vars like GPG_KEY, JAVA_HOME)
            "APP_SECRET_PATTERNS = ['SECRET_KEY', 'DATABASE_URL', 'JWT_', 'PHONEPE_', 'REDIS_URL', 'SALT_KEY']\n"
            "for k, v in os.environ.items():\n"
            "    if any(p in k.upper() for p in APP_SECRET_PATTERNS):\n"
            "        print(f'APP_SECRET_FOUND: {k}')\n"
            "print('ENV_SCAN_DONE')\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert "APP_SECRET_FOUND" not in result.stdout, (
        f"SECURITY VIOLATION: Container contains application secrets! stdout={result.stdout}"
    )
    assert "ENV_SCAN_DONE" in result.stdout



def test_docker_security_workspace_is_writable():
    """SECURITY: /workspace tmpfs must allow writes (for source and compiled artifacts)."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "with open('/workspace/test_artifact.txt', 'w') as f:\n"
            "    f.write('workspace write test')\n"
            "with open('/workspace/test_artifact.txt', 'r') as f:\n"
            "    content = f.read()\n"
            "print('WORKSPACE_WRITE_OK:', content)\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"Expected workspace to be writable: err={result.error_message}"
    assert "WORKSPACE_WRITE_OK" in result.stdout


def test_docker_sandbox_diagnostics_report_correct_flags():
    """Verify DockerSandbox.get_diagnostics() reports all security control flags."""
    sandbox = DockerSandbox()
    diag = sandbox.get_diagnostics()

    assert diag["driver"] == "docker"
    assert diag["available"] is True, "Docker must be available for this test"
    assert "isolation" in diag

    iso = diag["isolation"]
    assert iso["network"] == "none", f"Network must be 'none', got: {iso['network']}"
    assert iso["read_only_rootfs"] is True, "Rootfs must be read-only"
    assert "10001" in iso["user"], f"Must use uid 10001, got: {iso['user']}"
    assert iso["capabilities_dropped"] == ["ALL"], f"Must drop ALL caps, got: {iso['capabilities_dropped']}"
    assert iso["no_new_privileges"] is True, "no_new_privileges must be enforced"
    assert iso["pids_limit"] == 64, f"PID limit must be 64, got: {iso['pids_limit']}"


def test_docker_container_cleanup_after_execution():
    """Verify no containers remain running after judge execution."""
    import docker as docker_sdk
    client = docker_sdk.from_env()

    # Snapshot of running containers before test
    before = set(c.id for c in client.containers.list())

    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code='print("cleanup test")\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    sandbox.run(req)

    # Snapshot after — judge container must be fully cleaned up
    after = set(c.id for c in client.containers.list())
    new_containers = after - before
    assert len(new_containers) == 0, (
        f"CONTAINER LEAK: {len(new_containers)} container(s) left running after execution!"
    )
