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


class DockerSandbox(BaseSandbox):
    """Secure Docker Sandbox implementation.

    Source code is injected via base64 decode in the container command
    to avoid Docker put_archive conflicts with read_only=True rootfs.
    """

    def __init__(self) -> None:
        self._docker_client = None
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
        version_info = {}
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

    def _build_run_command(self, lang_def, source_code: str, stdin: str | None):
        """Builds shell command: decode source → write to workspace → [compile if needed] → run with stdin."""
        src_b64 = self._encode_source(source_code)
        stdin_b64 = self._encode_stdin(stdin)
        run_cmd = " ".join(lang_def.run_command)

        if lang_def.is_compiled and lang_def.compile_command:
            compile_cmd = " ".join(lang_def.compile_command)
            return [
                "sh",
                "-c",
                (
                    f"printf '%s' '{src_b64}' | base64 -d > /workspace/{lang_def.source_filename} && "
                    f"{compile_cmd} 2>/dev/null && "
                    f"printf '%s' '{stdin_b64}' | base64 -d | {run_cmd}"
                ),
            ]
        else:
            return [
                "sh",
                "-c",
                (
                    f"printf '%s' '{src_b64}' | base64 -d > /workspace/{lang_def.source_filename} && "
                    f"printf '%s' '{stdin_b64}' | base64 -d | {run_cmd}"
                ),
            ]

    def _create_container(self, image: str, command, mem_limit_mb: int):
        """Creates a secured, isolated Docker container with all security constraints."""
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
            mem_limit = max(request.memory_limit_mb or 256, 256)
            container = self._create_container(
                lang_def.docker_image, command, mem_limit
            )
            container.start()

            # 30s hard compilation timeout
            try:
                result = container.wait(timeout=30.0)
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

        try:
            command = self._build_run_command(
                lang_def, request.source_code, request.stdin
            )
            mem_limit = request.memory_limit_mb or lang_def.default_memory_limit_mb
            container = self._create_container(
                lang_def.docker_image, command, mem_limit
            )
            container.start()

            # Wait for execution with wall-clock timeout buffer (+1.0s)
            timed_out = False
            try:
                wait_res = container.wait(timeout=time_limit_sec + 1.0)
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

            output_limit = request.output_limit_bytes or MAX_SAFE_OUTPUT_BYTES
            output_exceeded = len(out_str.encode("utf-8")) > output_limit
            if output_exceeded:
                out_str = (
                    out_str[:output_limit] + "\n[OUTPUT TRUNCATED: Limit Exceeded]"
                )

            # Check TLE: container wait timed out OR elapsed exceeds configured limit
            if timed_out or elapsed_ms > request.time_limit_ms:
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
            return ExecutionResult(
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
