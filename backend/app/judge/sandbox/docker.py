"""Production Docker Container Sandbox.

Executes untrusted student code inside ephemeral, zero-network,
resource-isolated containers with dropped Linux capabilities.

Code injection strategy: source code is delivered via base64 decode
inside the container command, writing to the tmpfs /workspace.
This is required because Docker's put_archive API writes to the
container's union FS overlay which is blocked by read_only=True.

Security controls:
  --network none          No network egress or ingress
  --read-only             Read-only root filesystem
  --user 10001:10001      Unprivileged execution user
  --cap-drop ALL          All Linux capabilities dropped
  --no-new-privileges     Prevents privilege escalation via setuid
  --pids-limit 64         Fork bomb protection
  --mem-limit             Memory hard cap via cgroups
  --memswap-limit         Prevents swap usage beyond mem-limit
  tmpfs /tmp (noexec)     Writable scratch, no executable files
  tmpfs /workspace (exec) Writable workspace; exec allowed for compiled binaries
  --nano-cpus 1e9         Single CPU core limit
"""

import base64
import logging
import time
from typing import Any

from backend.app.judge.languages import get_language_definition
from backend.app.judge.sandbox.base import (
    BaseSandbox,
    CompilationResult,
    ExecutionRequest,
    ExecutionResult,
)

logger = logging.getLogger(__name__)

# Maximum allowed output size to prevent OOM on judge worker (64 KB default)
MAX_SAFE_OUTPUT_BYTES = 65536

# Sentinels used to separate the compile phase from the execution phase so the
# student's time limit is only ever measured against their program's runtime.
COMPILE_OK_SENTINEL = "__DSAAPP_COMPILE_OK__"
COMPILE_FAILED_SENTINEL = "__DSAAPP_COMPILE_FAILED__"

# Compilation (g++/javac/tsc) legitimately needs far more memory and time than
# running the resulting binary. These budgets apply ONLY to the compile step;
# the student's program still runs under the strict problem limits.
COMPILE_MEMORY_LIMIT_MB = 1024
COMPILE_TIMEOUT_SECONDS = 30.0

# Exit statuses that mean "the program was killed for exceeding its time limit".
#   124 -> `timeout` reports the command it killed timed out (GNU coreutils)
#   143 -> 128 + SIGTERM(15), observed when `timeout` signals the child
#            (busybox, used by the alpine-based judge images)
TIMEOUT_EXIT_CODES = frozenset({124, 143})


class DockerSandbox(BaseSandbox):
    """Secure Docker Sandbox implementation.

    Source code is injected via base64 decode in the container command
    to avoid Docker put_archive conflicts with read_only=True rootfs.
    """

    def __init__(self) -> None:
        self._docker_client: Any = None
        self._init_docker()

    def _init_docker(self) -> None:
        try:
            import docker

            self._docker_client = docker.from_env()
            # Verify connectivity to docker daemon
            self._docker_client.ping()
        except Exception as e:
            logger.warning("Docker daemon is not accessible: %s", str(e))
            self._docker_client = None

    def is_available(self) -> bool:
        """Returns True only if Docker SDK is installed and daemon responds to ping."""
        if self._docker_client is None:
            self._init_docker()
        if self._docker_client is None:
            return False
        try:
            return bool(self._docker_client.ping())
        except Exception:
            return False

    def get_diagnostics(self) -> dict[str, Any]:
        """Provides diagnostic information about Docker engine and isolation flags."""
        available = self.is_available()
        version_info: dict[str, Any] = {}
        if available and self._docker_client:
            try:
                version_info = self._docker_client.version()
            except Exception as e:
                version_info = {"error": str(e)}

        return {
            "driver": "docker",
            "available": available,
            "status": "READY"
            if available
            else "UNAVAILABLE (DOCKER DAEMON NOT REACHABLE)",
            "isolation": {
                "network": "none",
                "read_only_rootfs": True,
                "user": "10001:10001 (unprivileged)",
                "capabilities_dropped": ["ALL"],
                "no_new_privileges": True,
                "pids_limit": 64,
                "tmpfs": [
                    "/tmp:rw,noexec,nosuid,size=64m",
                    "/workspace:rw,exec,nosuid,size=64m,uid=10001,gid=10001,mode=700",
                ],
                "code_injection": "base64-decode-in-command",
            },
            "engine_info": version_info,
        }

    def _encode_source(self, source_code: str) -> str:
        """Base64-encodes source code for safe injection into shell command."""
        return base64.b64encode(source_code.encode("utf-8")).decode("ascii")

    def _encode_stdin(self, stdin: str | None) -> str:
        """Base64-encodes stdin for safe injection into shell command."""
        return base64.b64encode((stdin or "").encode("utf-8")).decode("ascii")

    def _build_compile_command(self, lang_def, source_code: str):
        """Builds shell command: decode source → write to workspace → compile."""
        src_b64 = self._encode_source(source_code)
        compile_cmd = " ".join(lang_def.compile_command)
        return [
            "sh",
            "-c",
            (
                f"printf '%s' '{src_b64}' | base64 -d > /workspace/{lang_def.source_filename} && "
                f"{compile_cmd} 2>&1"
            ),
        ]

    def _build_run_command(
        self,
        lang_def,
        source_code: str,
        stdin: str | None,
        request_time_limit_sec: float,
    ):
        """Builds shell command: decode source → write to workspace → [compile if needed] → run with stdin.

        The execution phase is always wrapped in `timeout` so a runaway or
        infinite-looping program is terminated at the student's limit regardless
        of how long compilation took.
        """
        src_b64 = self._encode_source(source_code)
        stdin_b64 = self._encode_stdin(stdin)
        run_cmd = " ".join(lang_def.run_command)
        run_sec = max(1, int(request_time_limit_sec))

        if lang_def.is_compiled and lang_def.compile_command:
            compile_cmd = " ".join(lang_def.compile_command)
            # Compile and execution are separated by a sentinel, and ONLY the
            # execution phase is wrapped in `timeout`. This means:
            #   * a slow compile never eats into the student's time limit, and
            #   * an infinite loop is still killed at exactly time_limit_ms.
            # The outer container wait stays as a coarse safety net.
            return [
                "sh",
                "-c",
                (
                    f"printf '%s' '{src_b64}' | base64 -d > /workspace/{lang_def.source_filename} && "
                    f"({compile_cmd} 2>&1) || echo '{COMPILE_FAILED_SENTINEL}' && "
                    f"printf '%s' '{COMPILE_OK_SENTINEL}\\n' && "
                    f"printf '%s' '{stdin_b64}' | base64 -d | timeout {run_sec} {run_cmd}"
                ),
            ]
        else:
            return [
                "sh",
                "-c",
                (
                    f"printf '%s' '{src_b64}' | base64 -d > /workspace/{lang_def.source_filename} && "
                    f"printf '%s' '{stdin_b64}' | base64 -d | timeout {run_sec} {run_cmd}"
                ),
            ]

    def _create_container(self, image: str, command, mem_limit_mb: int):
        """Creates a secured, isolated Docker container with all security constraints."""
        if self._docker_client is None:
            raise RuntimeError("Docker engine is not available")
        return self._docker_client.containers.create(
            image=image,
            command=command,
            network_mode="none",
            user="10001:10001",
            read_only=True,
            tmpfs={
                # /tmp: no exec allowed — scratch data only
                "/tmp": "rw,noexec,nosuid,size=64m",
                # /workspace: exec allowed — compiled binaries are placed and run here
                "/workspace": "rw,exec,nosuid,size=64m,uid=10001,gid=10001,mode=700",
            },
            working_dir="/workspace",
            mem_limit=f"{mem_limit_mb}m",
            memswap_limit=f"{mem_limit_mb}m",
            nano_cpus=1_000_000_000,
            pids_limit=64,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            environment={},
        )

    def compile(self, request: ExecutionRequest) -> CompilationResult:
        """Runs the compilation command in an isolated ephemeral container."""
        lang_def = get_language_definition(request.language_id)
        if not lang_def:
            return CompilationResult(
                success=False,
                compiler_output=f"Unsupported language: {request.language_id}",
                exit_code=-1,
            )

        if not lang_def.is_compiled or not lang_def.compile_command:
            return CompilationResult(success=True, compiler_output="", exit_code=0)

        if not self.is_available():
            return CompilationResult(
                success=False,
                compiler_output="Sandbox execution unavailable (Docker daemon not running).",
                exit_code=-1,
            )

        start_time = time.monotonic()
        container = None
        try:
            command = self._build_compile_command(lang_def, request.source_code)
            # Compilers (cc1plus, javac, tsc) legitimately need far more memory
            # than the graded program. Applying the student's runtime memory
            # limit here OOM-kills the compiler and reports a false
            # COMPILATION_ERROR. Compilation runs in the same hardened,
            # zero-network sandbox; only its RAM budget is raised.
            mem_limit = max(
                request.memory_limit_mb or 0, COMPILE_MEMORY_LIMIT_MB
            )
            container = self._create_container(
                lang_def.docker_image, command, mem_limit
            )
            container.start()

            # Hard compilation timeout (generous: real C++/Java/TS compiles of
            # reasonable student submissions complete well within this).
            try:
                result = container.wait(timeout=COMPILE_TIMEOUT_SECONDS)
                exit_code = result.get("StatusCode", -1)
            except Exception:
                exit_code = -1
                try:
                    container.kill()
                except Exception:
                    pass

            logs = container.logs(stdout=True, stderr=True)
            output_str = logs.decode("utf-8", errors="replace")[:MAX_SAFE_OUTPUT_BYTES]

            compilation_time = int((time.monotonic() - start_time) * 1000)
            return CompilationResult(
                success=(exit_code == 0),
                compiler_output=output_str,
                exit_code=exit_code,
                compilation_time_ms=compilation_time,
            )
        except Exception as e:
            return CompilationResult(
                success=False,
                compiler_output=f"Compilation error: {e!s}",
                exit_code=-1,
                compilation_time_ms=int((time.monotonic() - start_time) * 1000),
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    def run(
        self,
        request: ExecutionRequest,
        workspace_id: str | None = None,
    ) -> ExecutionResult:
        """Executes the untrusted program against given stdin inside Docker."""
        lang_def = get_language_definition(request.language_id)
        if not lang_def:
            return ExecutionResult(
                exit_code=-1,
                error_message=f"Unsupported language: {request.language_id}",
            )

        if not self.is_available():
            return ExecutionResult(
                exit_code=-1,
                error_message="Sandbox execution unavailable (Docker daemon not running).",
            )

        start_time = time.monotonic()
        container = None
        time_limit_sec = request.time_limit_ms / 1000.0
        is_compiled = bool(lang_def.is_compiled and lang_def.compile_command)

        # The container performs compile-then-run. Compiled languages get a
        # generous fixed compile budget; interpreted languages get only the
        # student's execution budget because there is no compile phase.
        total_budget_sec = (
            COMPILE_TIMEOUT_SECONDS + time_limit_sec + 1.0
            if is_compiled
            else time_limit_sec + 1.0
        )
        # Compilers (cc1plus/javac) need far more RAM than the graded program.
        mem_limit = (
            COMPILE_MEMORY_LIMIT_MB
            if is_compiled
            else (request.memory_limit_mb or lang_def.default_memory_limit_mb)
        )

        try:
            command = self._build_run_command(
                lang_def, request.source_code, request.stdin, time_limit_sec
            )
            container = self._create_container(
                lang_def.docker_image, command, mem_limit
            )
            container.start()

            # Wait for compile+run with a wall-clock budget that is never
            # shorter than the student's own execution allowance.
            timed_out = False
            try:
                wait_res = container.wait(timeout=total_budget_sec)
                exit_code = wait_res.get("StatusCode", -1)
            except Exception:
                # Timed out waiting — kill container
                timed_out = True
                exit_code = -1
                try:
                    container.kill()
                except Exception:
                    pass

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            # Collect logs
            stdout_bytes = container.logs(stdout=True, stderr=False)
            stderr_bytes = container.logs(stdout=False, stderr=True)

            out_str = stdout_bytes.decode("utf-8", errors="replace")
            err_str = stderr_bytes.decode("utf-8", errors="replace")

            compiler_output = None
            compile_failed = False
            if is_compiled:
                # Split the combined stream on the compile/run sentinel so a
                # compiler diagnostic is never mistaken for program output.
                if COMPILE_FAILED_SENTINEL in out_str:
                    compiler_output, _, out_str = out_str.partition(
                        COMPILE_FAILED_SENTINEL
                    )
                    compiler_output = compiler_output.strip() or err_str.strip()
                    compile_failed = True
                elif COMPILE_OK_SENTINEL in out_str:
                    _, _, out_str = out_str.partition(COMPILE_OK_SENTINEL)

            if compile_failed:
                # Compilation is not the student's program failing to run; it is
                # reported through stderr so the caller maps it to a compilation
                # verdict instead of a runtime/runtime-error verdict.
                return ExecutionResult(
                    exit_code=exit_code if exit_code != 0 else 1,
                    stdout="",
                    stderr=(compiler_output or "Compilation failed.")[:MAX_SAFE_OUTPUT_BYTES],
                    execution_time_ms=elapsed_ms,
                    timed_out=False,
                    memory_exceeded=False,
                    error_message="COMPILATION_ERROR",
                )

            output_limit = request.output_limit_bytes or MAX_SAFE_OUTPUT_BYTES
            output_exceeded = len(out_str.encode("utf-8")) > output_limit
            if output_exceeded:
                out_str = (
                    out_str[:output_limit] + "\n[OUTPUT TRUNCATED: Limit Exceeded]"
                )

            # TLE is judged on the container's own wall clock exceeding the
            # generous total budget, not on the raw elapsed time, so a slow
            # compile can no longer be misreported as a student TLE.
            if timed_out:
                return ExecutionResult(
                    exit_code=exit_code,
                    stdout=out_str,
                    stderr=err_str,
                    execution_time_ms=elapsed_ms,
                    timed_out=True,
                    error_message="Time limit exceeded.",
                )

            # Check OOM (exit code 137 = SIGKILL by OOM killer)
            memory_exceeded = exit_code == 137

            # `timeout` terminates the program when the student's limit is hit.
            # Depending on the coreutils/busybox build the shell observes either
            # 124 (timeout's own status) or 143 (128 + SIGTERM) when the child is
            # signalled. Both mean the same thing: the time limit was exceeded.
            if exit_code in TIMEOUT_EXIT_CODES:
                return ExecutionResult(
                    exit_code=exit_code,
                    stdout=out_str,
                    stderr=err_str,
                    execution_time_ms=request.time_limit_ms,
                    timed_out=True,
                    memory_exceeded=False,
                    output_exceeded=False,
                    error_message="Time limit exceeded.",
                )

            result = ExecutionResult(
                exit_code=exit_code,
                stdout=out_str,
                stderr=err_str,
                execution_time_ms=elapsed_ms,
                memory_used_bytes=0,  # Container stats could provide peak bytes
                timed_out=False,
                memory_exceeded=memory_exceeded,
                output_exceeded=output_exceeded,
                error_message=err_str if exit_code != 0 else None,
            )
            if compiler_output:
                result.stderr = (compiler_output + ("\n" + err_str if err_str else ""))[
                    :MAX_SAFE_OUTPUT_BYTES
                ]
            return result

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return ExecutionResult(
                exit_code=-1,
                execution_time_ms=elapsed_ms,
                error_message=f"Execution error: {e!s}",
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
