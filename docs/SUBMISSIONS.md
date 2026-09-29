# Submissions & Source Code Architecture

## Overview
The submissions subsystem is designed to ingest, validate, deduplicate, and persist untrusted student source code while guaranteeing zero in-process execution risks.

---

## 1. Zero-Trust Security Invariants

### 1.1 In-Process Execution Prohibition
- **Absolute Invariant**: Student code is NEVER evaluated inside the FastAPI application process, web workers, Celery threads, or local shell environments.
- Functions such as `eval()`, `exec()`, `compile()`, and `subprocess.run()` on user input are strictly prohibited.
- Initial submission statuses are limited to:
  - `CREATED`
  - `QUEUED_FOR_FUTURE_JUDGE`
  - `NOT_EXECUTED`
  - `CANCELLED`
- Under no circumstances does Phase 4 return fabricated verdicts such as "Accepted" or "Passed 10/10 test cases".

### 1.2 Data Sanitization & Constraints
- **Payload Size Limit**: Maximum 64 KB (65,536 UTF-8 encoded bytes). Enforced at both Pydantic schema validation and frontend input handlers.
- **Language Allowlist**:
  - `python`
  - `javascript`
  - `typescript`
  - `java`
  - `cpp`
  Requests specifying arbitrary or unknown compilers/interpreters are rejected with HTTP 422.
- **Log Privacy & Data Leakage Prevention**: Untrusted student code is NEVER written to application stdout, log aggregators, or `audit_logs` metadata.
- **List Query Protection**: `GET /api/v1/submissions` returns lightweight summaries (`SubmissionSummary`) that strictly omit `source_code`. Full code is only returned when fetching a specific submission detail (`GET /api/v1/submissions/{id}`).

### 1.3 Idempotency & Deduplication
- Submissions support an optional HTTP header: `Idempotency-Key`.
- When an `Idempotency-Key` is supplied, the system checks whether a submission with that key already exists for the user. If found, the existing record is returned with HTTP 200 without creating a duplicate database entry.

---

## 2. Database Model: `Submission`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | VARCHAR(36) | Primary Key | Internal UUID |
| `public_id` | VARCHAR(36) | Unique, Indexed | Public alphanumeric identifier (`sub_...`) |
| `user_id` | VARCHAR(36) | Foreign Key, Indexed | Owning user (`users.id`) |
| `problem_id` | VARCHAR(36) | Foreign Key, Indexed | Targeted problem (`problems.id`) |
| `language` | VARCHAR(32) | Not Null | Programming language string |
| `source_code` | TEXT | Not Null | Raw source code (max 64KB) |
| `status` | ENUM | Not Null | `QUEUED_FOR_FUTURE_JUDGE`, etc. |
| `idempotency_key` | VARCHAR(128) | Nullable, Indexed | Deduplication key |
| `execution_notice` | VARCHAR(255) | Not Null | Static educational disclaimer |
| `created_at` | TIMESTAMP | Not Null | Submission UTC creation timestamp |
| `updated_at` | TIMESTAMP | Not Null | UTC update timestamp |

---

## 3. Future Online Judge Integration Boundary (Phase 7)
In Phase 7, a distributed worker pool with containerized Linux sandboxes (cgroups v2, seccomp, network isolation, drop all capabilities) will poll the submission queue or consume a Redis Streams / RabbitMQ event topic to compile and execute submissions against hidden verification suites.
