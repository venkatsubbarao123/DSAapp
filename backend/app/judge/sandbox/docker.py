"""Production Docker Container Sandbox.

Executes untrusted student code inside ephemeral, zero-network,
resource-isolated containers with dropped Linux capabilities.
"""

import io
import logging
import tarfile
import time
from typing import Any, Dict, Optional, Tuple

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
    """Secure Docker Sandbox implementation."""

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

    def get_diagnostics(self) -> Dict[str, Any]:
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
            "status": "READY" if available else "UNAVAILABLE (DOCKER DAEMON NOT REACHABLE)",
            "isolation": {
                "network": "none",
                "read_only_rootfs": True,
                "user": "10001:10001 (unprivileged)",
                "capabilities_dropped": ["ALL"],
                "no_new_privileges": True,
                "pids_limit": 64,
                "tmpfs": ["/tmp:rw,noexec,nosuid,size=64m", "/workspace:rw,nosuid,size=64m"],
            },
            "engine_info": version_info,
        }

    def _create_tar_archive(self, filename: str, content: str) -> io.BytesIO:
        """Packages file content into an in-memory tar stream for docker put_archive."""
        data = content.encode("utf-8")
        tar_stream = io.BytesIO()
        with tarfile.open(fileobj=tar_stream, mode="w") as tar:
            tarinfo = tarfile.TarInfo(name=filename)
            tarinfo.size = len(data)
            tarinfo.mtime = int(time.time())
            tarinfo.mode = 0o644
            tar.addfile(tarinfo, io.BytesIO(data))
        tar_stream.seek(0)
        return tar_stream

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
            # Ephemeral compilation container
            container = self._docker_client.containers.create(
                image=lang_def.docker_image,
                command=lang_def.compile_command,
                network_mode="none",
                user="10001:10001",
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m", "/workspace": "rw,nosuid,size=64m"},
                working_dir="/workspace",
                mem_limit=f"{max(request.memory_limit_mb, 256)}m",
                memswap_limit=f"{max(request.memory_limit_mb, 256)}m",
                nano_cpus=1000000000,
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                environment={},
            )

            # Copy source file into container workspace
            tar_data = self._create_tar_archive(lang_def.source_filename, request.source_code)
            container.put_archive("/workspace", tar_data)

            container.start()
            # 15s hard compilation timeout
            result = container.wait(timeout=15.0)
            exit_code = result.get("StatusCode", -1)

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
                compiler_output=f"Compilation error: {str(e)}",
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
        workspace_id: Optional[str] = None,
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
            container = self._docker_client.containers.create(
                image=lang_def.docker_image,
                command=lang_def.run_command,
                stdin_open=True,
                network_mode="none",
                user="10001:10001",
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m", "/workspace": "rw,nosuid,size=64m"},
                working_dir="/workspace",
                mem_limit=f"{request.memory_limit_mb}m",
                memswap_limit=f"{request.memory_limit_mb}m",
                nano_cpus=1000000000,
                pids_limit=64,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                environment={},
            )

            # Copy source file
            tar_data = self._create_tar_archive(lang_def.source_filename, request.source_code)
            container.put_archive("/workspace", tar_data)

            container.start()

            # Pipe stdin if provided
            socket = container.attach_socket(params={"stdin": 1, "stream": 1})
            if request.stdin:
                socket._sock.sendall(request.stdin.encode("utf-8"))
            socket._sock.shutdown(1)

            # Wait for execution with wall-clock timeout buffer (+1.0s)
            timed_out = False
            try:
                wait_res = container.wait(timeout=time_limit_sec + 1.0)
                exit_code = wait_res.get("StatusCode", -1)
            except Exception:
                # Timed out waiting
                timed_out = True
                exit_code = -1
                try:
                    container.kill()
                except Exception:
                    pass

            elapsed_ms = int((time.monotonic() - start_time) * 1000)

            # Get logs
            logs = container.logs(stdout=True, stderr=False)
            err_logs = container.logs(stdout=False, stderr=True)

            out_str = logs.decode("utf-8", errors="replace")
            err_str = err_logs.decode("utf-8", errors="replace")

            output_limit = request.output_limit_bytes or MAX_SAFE_OUTPUT_BYTES
            output_exceeded = len(out_str.encode("utf-8")) > output_limit
            if output_exceeded:
                out_str = out_str[:output_limit] + "\n[OUTPUT TRUNCATED: Limit Exceeded]"

            # Check TLE
            if timed_out or elapsed_ms > request.time_limit_ms:
                return ExecutionResult(
                    exit_code=exit_code,
                    stdout=out_str,
                    stderr=err_str,
                    execution_time_ms=elapsed_ms,
                    timed_out=True,
                    error_message="Time limit exceeded.",
                )

            # Check OOM (exit code 137 typically indicates killed by SIGKILL / OOM)
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
                error_message=f"Execution error: {str(e)}",
            )
        finally:
            if container:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
