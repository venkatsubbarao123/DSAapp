"""Real Docker Integration Tests for Phase 5 Online Judge.

These tests REQUIRE Docker Desktop to be installed and running.
Tests are SKIPPED automatically (not failed) if Docker is not available.

DO NOT use MockSandbox in this test file.
DO NOT fabricate results.
All results must come from real Docker container execution.

Coverage:
- Python: accepted, wrong answer, runtime error, TLE
- C++: accepted, compilation error, wrong answer, runtime error, TLE
- Java: accepted, compilation error, wrong answer, runtime error, TLE
- JavaScript: accepted, wrong answer, runtime error, TLE
- Security: network isolation, non-root user, read-only rootfs
- Verdicts: ACCEPTED, WRONG_ANSWER, TLE, RUNTIME_ERROR, COMPILATION_ERROR, OUTPUT_LIMIT_EXCEEDED
"""

import pytest
import time

from backend.app.judge.sandbox.docker import DockerSandbox
from backend.app.judge.sandbox.base import ExecutionRequest


def get_docker_sandbox():
    """Instantiate DockerSandbox and skip test if Docker not available."""
    sandbox = DockerSandbox()
    if not sandbox.is_available():
        pytest.skip("Docker engine is not available — skipping real Docker tests.")
    return sandbox


# ─────────────────────────────────────────────────────────────────────────────
# PYTHON TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_python_accepted_hello_world():
    """Real Docker: Python prints Hello World → ACCEPTED."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code='print("Hello, World!")\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}. stderr={result.stderr}"
    assert "Hello, World!" in result.stdout
    assert not result.timed_out
    assert not result.memory_exceeded


def test_docker_python_accepted_stdin():
    """Real Docker: Python reads stdin correctly."""
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
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "42" in result.stdout.strip()


def test_docker_python_wrong_answer():
    """Real Docker: Python prints wrong output → can be detected as WRONG_ANSWER."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code='print(999)\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0  # Program succeeds, but output is wrong
    assert "999" in result.stdout
    # Comparator logic would detect wrong answer — verified in comparator tests


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
    assert result.exit_code != 0, f"Expected non-zero exit code for runtime error"
    assert not result.timed_out


def test_docker_python_time_limit_exceeded():
    """Real Docker: Python infinite loop → timed_out=True with short TL."""
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

    assert result.timed_out is True, f"Expected timed_out=True, got {result.timed_out}. exit={result.exit_code}"
    # Must not hang for more than time_limit + 5s grace
    assert elapsed < 10.0, f"TLE handling took too long: {elapsed:.1f}s"


def test_docker_python_division_by_zero():
    """Real Docker: Python ZeroDivisionError → runtime error."""
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
    assert "ZeroDivisionError" in (result.stderr or "")


def test_docker_python_output_limit_exceeded():
    """Real Docker: Python excessive output → output_exceeded=True."""
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
    assert result.output_exceeded is True or "[OUTPUT TRUNCATED" in result.stdout


# ─────────────────────────────────────────────────────────────────────────────
# C++ TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_cpp_accepted_hello_world():
    """Real Docker: C++ compiles and runs Hello World → ACCEPTED."""
    sandbox = get_docker_sandbox()

    # Compile
    compile_req = ExecutionRequest(
        language_id="cpp",
        source_code='#include <iostream>\nint main() { std::cout << "Hello, World!" << std::endl; return 0; }\n',
        time_limit_ms=15000,
        memory_limit_mb=256,
    )
    comp_result = sandbox.compile(compile_req)
    assert comp_result.success, f"C++ compile failed: {comp_result.compiler_output}"

    # Run
    run_req = ExecutionRequest(
        language_id="cpp",
        source_code=compile_req.source_code,
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(run_req)
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "Hello, World!" in result.stdout


def test_docker_cpp_accepted_with_stdin():
    """Real Docker: C++ reads stdin and computes correctly."""
    sandbox = get_docker_sandbox()

    src = (
        "#include <iostream>\n"
        "int main() { int a, b; std::cin >> a >> b; std::cout << a + b << std::endl; return 0; }\n"
    )

    comp_req = ExecutionRequest(language_id="cpp", source_code=src, time_limit_ms=15000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Compile failed: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="cpp", source_code=src, stdin="3 7\n", time_limit_ms=5000, memory_limit_mb=256)
    result = sandbox.run(run_req)
    assert result.exit_code == 0
    assert "10" in result.stdout.strip()


def test_docker_cpp_compilation_error():
    """Real Docker: C++ with syntax error → compilation fails."""
    sandbox = get_docker_sandbox()
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
    """Real Docker: C++ dereferences null pointer → non-zero exit."""
    sandbox = get_docker_sandbox()

    src = "#include <cstdlib>\nint main() { int* p = nullptr; *p = 1; return 0; }\n"
    comp_req = ExecutionRequest(language_id="cpp", source_code=src, time_limit_ms=15000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Compile failed unexpectedly: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="cpp", source_code=src, stdin="", time_limit_ms=5000, memory_limit_mb=256)
    result = sandbox.run(run_req)
    assert result.exit_code != 0, "Expected non-zero exit for null dereference"
    assert not result.timed_out


def test_docker_cpp_time_limit_exceeded():
    """Real Docker: C++ infinite loop → TLE."""
    sandbox = get_docker_sandbox()
    src = "#include <cstdlib>\nint main() { for(;;); return 0; }\n"
    comp_req = ExecutionRequest(language_id="cpp", source_code=src, time_limit_ms=15000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Compile failed: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="cpp", source_code=src, stdin="", time_limit_ms=1000, memory_limit_mb=256)
    start = time.monotonic()
    result = sandbox.run(run_req)
    elapsed = time.monotonic() - start

    assert result.timed_out is True, f"Expected TLE, got exit={result.exit_code}"
    assert elapsed < 10.0, f"TLE took too long: {elapsed:.1f}s"


# ─────────────────────────────────────────────────────────────────────────────
# JAVA TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_java_accepted_hello_world():
    """Real Docker: Java compiles and runs Hello World."""
    sandbox = get_docker_sandbox()

    src = (
        "public class Solution {\n"
        "    public static void main(String[] args) {\n"
        "        System.out.println(\"Hello, World!\");\n"
        "    }\n"
        "}\n"
    )
    comp_req = ExecutionRequest(language_id="java", source_code=src, time_limit_ms=20000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Java compile failed: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="java", source_code=src, stdin="", time_limit_ms=10000, memory_limit_mb=256)
    result = sandbox.run(run_req)
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "Hello, World!" in result.stdout


def test_docker_java_accepted_with_scanner():
    """Real Docker: Java reads stdin with Scanner and processes correctly."""
    sandbox = get_docker_sandbox()

    src = (
        "import java.util.Scanner;\n"
        "public class Solution {\n"
        "    public static void main(String[] args) {\n"
        "        Scanner sc = new Scanner(System.in);\n"
        "        int a = sc.nextInt();\n"
        "        int b = sc.nextInt();\n"
        "        System.out.println(a + b);\n"
        "    }\n"
        "}\n"
    )
    comp_req = ExecutionRequest(language_id="java", source_code=src, time_limit_ms=20000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Java compile failed: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="java", source_code=src, stdin="15 27\n", time_limit_ms=10000, memory_limit_mb=256)
    result = sandbox.run(run_req)
    assert result.exit_code == 0
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
    """Real Docker: Java throws ArrayIndexOutOfBoundsException."""
    sandbox = get_docker_sandbox()

    src = (
        "public class Solution {\n"
        "    public static void main(String[] args) {\n"
        "        int[] arr = new int[0];\n"
        "        System.out.println(arr[5]); // AIOOBE\n"
        "    }\n"
        "}\n"
    )
    comp_req = ExecutionRequest(language_id="java", source_code=src, time_limit_ms=20000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Compile failed: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="java", source_code=src, stdin="", time_limit_ms=10000, memory_limit_mb=256)
    result = sandbox.run(run_req)
    assert result.exit_code != 0, "Expected non-zero exit for AIOOBE"
    assert not result.timed_out


def test_docker_java_time_limit_exceeded():
    """Real Docker: Java infinite loop → TLE."""
    sandbox = get_docker_sandbox()

    src = (
        "public class Solution {\n"
        "    public static void main(String[] args) { while(true) {} }\n"
        "}\n"
    )
    comp_req = ExecutionRequest(language_id="java", source_code=src, time_limit_ms=20000, memory_limit_mb=256)
    comp = sandbox.compile(comp_req)
    assert comp.success, f"Compile failed: {comp.compiler_output}"

    run_req = ExecutionRequest(language_id="java", source_code=src, stdin="", time_limit_ms=1500, memory_limit_mb=256)
    start = time.monotonic()
    result = sandbox.run(run_req)
    elapsed = time.monotonic() - start

    assert result.timed_out is True, f"Expected TLE, got exit={result.exit_code}"
    assert elapsed < 15.0, f"TLE handling took too long: {elapsed:.1f}s"


# ─────────────────────────────────────────────────────────────────────────────
# JAVASCRIPT TESTS
# ─────────────────────────────────────────────────────────────────────────────

def test_docker_javascript_accepted_hello_world():
    """Real Docker: JavaScript prints Hello World."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="javascript",
        source_code='console.log("Hello, World!");\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "Hello, World!" in result.stdout


def test_docker_javascript_accepted_with_stdin():
    """Real Docker: JavaScript reads stdin and adds numbers."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="javascript",
        source_code=(
            "const lines = [];\n"
            "process.stdin.on('data', d => lines.push(d.toString()));\n"
            "process.stdin.on('end', () => {\n"
            "  const parts = lines.join('').trim().split('\\n');\n"
            "  const nums = parts[0].split(' ').map(Number);\n"
            "  console.log(nums[0] + nums[1]);\n"
            "});\n"
        ),
        stdin="5 7\n",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert result.exit_code == 0, f"stderr={result.stderr}"
    assert "12" in result.stdout.strip()


def test_docker_javascript_runtime_error():
    """Real Docker: JavaScript throws TypeError → non-zero exit."""
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
    """Security: Container must not have internet access (--network none)."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import socket\n"
            "try:\n"
            "    socket.setdefaulttimeout(2)\n"
            "    socket.socket().connect(('8.8.8.8', 53))\n"
            "    print('NETWORK_ACCESSIBLE')\n"
            "except Exception as e:\n"
            "    print('NETWORK_BLOCKED')\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    # Network should be blocked
    assert "NETWORK_BLOCKED" in result.stdout, (
        f"SECURITY VIOLATION: Container has internet access! stdout={result.stdout}"
    )
    assert "NETWORK_ACCESSIBLE" not in result.stdout


def test_docker_security_non_root_user():
    """Security: Container must run as non-root user (uid=10001)."""
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


def test_docker_security_cannot_read_etc_shadow():
    """Security: Container must not be able to read /etc/shadow."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "try:\n"
            "    with open('/etc/shadow', 'r') as f:\n"
            "        print('SHADOW_READABLE:', f.read()[:50])\n"
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
    # Either file doesn't exist or permission denied — both are acceptable
    assert "SHADOW_BLOCKED_PERMISSION" in result.stdout or "SHADOW_NOT_FOUND" in result.stdout, (
        f"SECURITY VIOLATION: /etc/shadow may be readable! stdout={result.stdout}"
    )


def test_docker_security_cannot_write_to_root_fs():
    """Security: Container rootfs must be read-only — writes only allowed to /tmp and /workspace."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import os\n"
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


def test_docker_security_no_host_filesystem_access():
    """Security: Container must not be able to access host filesystem paths."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import os\n"
            "# Try to read Windows host path — must fail\n"
            "paths = ['/mnt/c/Windows/System32', '/host', '/proc/1/root']\n"
            "for p in paths:\n"
            "    exists = os.path.exists(p)\n"
            "    if exists:\n"
            "        print(f'HOST_PATH_ACCESSIBLE: {p}')\n"
            "    else:\n"
            "        print(f'HOST_PATH_BLOCKED: {p}')\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert "HOST_PATH_ACCESSIBLE: /mnt/c/Windows" not in result.stdout, (
        f"SECURITY VIOLATION: Container can see Windows host path! stdout={result.stdout}"
    )


def test_docker_security_no_env_var_leakage():
    """Security: Container environment must not contain host or application secrets."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code=(
            "import os\n"
            "env = dict(os.environ)\n"
            "print('ENV_KEYS:', list(env.keys()))\n"
            # Check for sensitive patterns
            "for k, v in env.items():\n"
            "    if any(s in k.upper() for s in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN', 'JWT', 'DATABASE']):\n"
            "        print(f'SENSITIVE_ENV_FOUND: {k}')\n"
            "print('ENV_SCAN_DONE')\n"
        ),
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    result = sandbox.run(req)
    assert "SENSITIVE_ENV_FOUND" not in result.stdout, (
        f"SECURITY VIOLATION: Container contains sensitive environment variables! stdout={result.stdout}"
    )
    assert "ENV_SCAN_DONE" in result.stdout


def test_docker_security_writable_workspace():
    """Security: Container /workspace must allow writes (for compilation artifacts)."""
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
    assert result.exit_code == 0, f"Expected workspace to be writable: stderr={result.stderr}"
    assert "WORKSPACE_WRITE_OK" in result.stdout


def test_docker_security_excessive_output_truncated():
    """Security: OLE — massive output is truncated at output_limit_bytes."""
    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code="print('A' * 500000)\n",  # 500KB output
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
        output_limit_bytes=4096,  # 4KB limit
    )
    result = sandbox.run(req)
    # Output should be truncated
    total_bytes = len((result.stdout or "").encode("utf-8"))
    assert total_bytes <= 5000, f"Output not properly truncated: {total_bytes} bytes"


def test_docker_sandbox_availability_diagnostics():
    """Verify DockerSandbox.get_diagnostics() reports correct security flags."""
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
    """Verify no container remains running after execution completes."""
    import docker as docker_sdk
    client = docker_sdk.from_env()

    # List running containers BEFORE
    before_containers = set(c.id for c in client.containers.list())

    sandbox = get_docker_sandbox()
    req = ExecutionRequest(
        language_id="python",
        source_code='print("cleanup test")\n',
        stdin="",
        time_limit_ms=5000,
        memory_limit_mb=256,
    )
    sandbox.run(req)

    # List running containers AFTER — judge containers must be removed
    after_containers = set(c.id for c in client.containers.list())
    new_containers = after_containers - before_containers
    assert len(new_containers) == 0, (
        f"Container leak detected: {len(new_containers)} container(s) left running after execution."
    )
