# Judge Worker & Asynchronous Queue Execution (Phase 5)

## 1. Overview

The `JudgeWorker` is an isolated worker process that continuously claims jobs from `JudgeQueue`, executes compilation and test suites within containerized sandboxes, persists results, and synchronizes user problem progress.

---

## 2. Job Execution Lifecycle

```mermaid
sequenceDiagram
    participant Queue as JudgeQueue
    participant Worker as JudgeWorker
    participant Sandbox as DockerSandbox
    participant DB as SQL Database

    Queue->>Worker: Atomic Claim (JudgeJob: RUNNING)
    Worker->>DB: Submission.status = RUNNING
    Worker->>DB: Send Heartbeat
    alt Compiled Language (C++, Java, TS)
        Worker->>Sandbox: compile(request)
        alt Compile Failed
            Sandbox-->>Worker: CompilationResult (fail)
            Worker->>DB: Verdict: COMPILATION_ERROR
            Worker->>Queue: Job Completed
        end
    end
    loop For each test case
        Worker->>DB: Send Heartbeat
        Worker->>Sandbox: run(request, stdin)
        Sandbox-->>Worker: ExecutionResult
        Worker->>Worker: compare_outputs(actual, expected)
        alt Mismatch or Error
            Worker->>Worker: Set Verdict (WA, TLE, MLE, RTE, OLE)
            Worker->>DB: Persist SubmissionResult
        end
    end
    alt All Tests Passed
        Worker->>DB: Verdict: ACCEPTED
        Worker->>DB: UserProblemProgress: SOLVED (solved_at = now)
    end
    Worker->>Queue: Job Completed
```

---

## 3. Worker Crash Recovery & Dead Job Reclamation

1. **Heartbeat Protocol**: Workers periodically update `heartbeat_at` on their claimed `JudgeJob` (default every 5 seconds).
2. **Reclamation**:
   - `JudgeQueue.reclaim_stale_jobs()` identifies jobs where `status == RUNNING` and `heartbeat_at < now - 30s`.
   - If `attempt_count < max_attempts`, re-queues job (`RETRY_PENDING`).
   - If `attempt_count >= max_attempts`, transitions to `FAILED` and sets submission status to `SYSTEM_ERROR`.
