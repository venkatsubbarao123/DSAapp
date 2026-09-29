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
container = docker_client.containers.create(
    image=lang_def.docker_image,
    command=lang_def.run_command,
    stdin_open=True,
    network_mode="none",
    user="10001:10001",
    read_only=True,
    tmpfs={
        "/tmp": "rw,noexec,nosuid,size=64m",
        "/workspace": "rw,nosuid,size=64m"
    },
    working_dir="/workspace",
    mem_limit=f"{memory_limit_mb}m",
    memswap_limit=f"{memory_limit_mb}m",
    nano_cpus=1000000000,  # 1.0 CPU Core
    pids_limit=64,
    cap_drop=["ALL"],
    security_opt=["no-new-privileges:true"],
    environment={},
)
```

---

## 3. Host Environment Probing & Anti-Fabrication Guarantee

Per Sections 39, 72, and 75 of the production specification:
- The system verifies the real presence and availability of the Docker daemon via `docker_client.ping()`.
- If the Docker daemon is absent or unreachable on the host operating system, `is_available()` returns `False`.
- The system NEVER fabricates container execution: jobs report `SYSTEM_ERROR` with diagnostic message `Sandbox execution unavailable: Docker daemon not reachable`.
