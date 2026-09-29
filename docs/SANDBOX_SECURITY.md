# Sandbox Security & Threat Mitigation Specification (Phase 5)

## 1. Threat Matrix & Defense Controls

| Attack Vector | Threat Impact | Mitigation Mechanism |
| :--- | :--- | :--- |
| **Fork Bombs** | Exhaust host PIDs and crash machine | Container `--pids-limit 64` bounds maximum concurrency. |
| **Memory Exhaustion (OOM)** | Degrade host node memory | Strict `mem_limit` and matching `memswap_limit` (swap disabled). |
| **Infinite Loops** | Max out CPU cores indefinitely | Container `nano_cpus=1.0` + wall-clock timeout killer. |
| **Network Egress / Exfiltration**| Phone-home attacks, crypto mining, botnets | `--network none` strictly drops all network interfaces except loopback. |
| **Filesystem Tampering / Persistence** | Trojan binaries, secret tampering | `--read-only` rootfs with ephemeral memory-backed `tmpfs`. |
| **Privilege Escalation** | Break out to host root | Non-root `user 10001:10001`, `cap_drop: ["ALL"]`, `no-new-privileges: true`. |
| **Secret Leaking** | Student steals DB/API/JWT tokens | Sandbox container has EMPTY environment (`environment={}`). No host mounts. |
| **Output Flooding** | DoS judge worker or UI with gigabyte stdout | `output_limit_bytes` (64KB default) truncates stdout and triggers OLE verdict. |

---

## 2. Docker Container Security Parameters

```python
# Code injection: source code is base64-encoded and decoded inside the container command.
# This is required because Docker's put_archive API writes to the union FS overlay
# which is blocked by read_only=True. Base64 decode writes directly to the tmpfs /workspace.
command = [
    "sh", "-c",
    f"printf '%s' '{src_b64}' | base64 -d > /workspace/{filename} && "
    f"printf '%s' '{stdin_b64}' | base64 -d | {run_command}"
]

container = docker_client.containers.create(
    image=lang_def.docker_image,
    command=command,
    network_mode="none",
    user="10001:10001",
    read_only=True,
    tmpfs={
        # /tmp: scratch data only — no executable files permitted
        "/tmp": "rw,noexec,nosuid,size=64m",
        # /workspace: source code and compiled binaries (exec required for C++/Java)
        "/workspace": "rw,exec,nosuid,size=64m,uid=10001,gid=10001,mode=700",
    },
    working_dir="/workspace",
    mem_limit=f"{memory_limit_mb}m",
    memswap_limit=f"{memory_limit_mb}m",
    nano_cpus=1_000_000_000,  # 1.0 CPU Core
    pids_limit=64,
    cap_drop=["ALL"],
    security_opt=["no-new-privileges:true"],
    environment={},
)
```

### tmpfs Mount Design

| Mount | Options | Rationale |
|---|---|---|
| `/tmp` | `noexec,nosuid` | Scratch area for data only; no executable creation |
| `/workspace` | `exec,nosuid,uid=10001,gid=10001,mode=700` | Allows execution of compiled binaries (C++, Java); owned exclusively by judge user |



---

## 3. Host Environment Probing & Anti-Fabrication Guarantee

Per Sections 39, 72, and 75 of the production specification:
- The system verifies the real presence and availability of the Docker daemon via `docker_client.ping()`.
- If the Docker daemon is absent or unreachable on the host operating system, `is_available()` returns `False`.
- The system NEVER fabricates container execution: jobs report `SYSTEM_ERROR` with diagnostic message `Sandbox execution unavailable: Docker daemon not reachable`.
