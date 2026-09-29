# DSAapp Security Architecture & Compliance Specification

## 1. Prime Directive: Student Code Execution Boundary

> [!CAUTION]
> **FastAPI MUST NEVER execute arbitrary student code.**
> **Student code must execute strictly outside the API process.**
> Any use of unrestricted `eval()`, `exec()`, or direct `subprocess.run()` against untrusted user code inside the API server process is strictly prohibited.

### Execution Isolation Controls (Target: Phase 7)
* **Status:** `PLANNED` (Architectural boundary established in Phase 1).
* **Isolation Engine:** Containerized sandbox runners (`ContainerizedSandboxRunner`) running with `--network none`, drop-all Linux capabilities, seccomp filters, and non-root users.
* **Local Development Engine:** `IsolatedProcessRunner` utilizing OS-level timeouts, restricted temporary workspaces, and memory limits when containers are unavailable.
* **Resource Limits:**
  * Memory ceiling: 256 MB hard limit.
  * CPU quota: 1 core limit with strict time bounds (1.5s–3.0s).
  * Process count: Maximum 64 PIDs to mitigate fork bombs.
  * Output buffer: Truncated at 64 KB to mitigate memory exhaustion from infinite printing loops.
* **Credential Isolation:** Sandbox containers and workers must **never** inherit environment variables containing database passwords, JWT secrets, AI API keys, or cloud credentials.

---

## 2. AI Security Boundary & Prompt Defense

```
Student / Client
      │
      ▼
Backend AI Controller (/api/v1/ai/*)  <── Enforces Rate Limits & User Auth
      │
      ▼
AI Service Layer                      <── Injects System Context & Guardrails
      │
      ▼
Provider Adapter                      <── Communicates via Backend-Only Secret
      │
      ▼
LLM Provider API (Google Gemini / Anthropic / OpenAI)
```

* **Status:** `PLANNED` (Target: Phases 8–10).
* **Client Key Isolation:** Frontend client source and browser environment variables will **never** contain LLM API keys.
* **Untrusted Input Assumption:** All prompt input and external context are treated as potentially adversarial.
* **Strict Output Schema:** AI responses are treated as untrusted data and must pass Pydantic schema validation prior to returning to clients or writing to storage.

---

## 3. Cryptography & Secrets Management

* **Secrets Storage:** All credentials (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, PhonePe keys, API keys) reside in environment variables. No secrets are committed to Git.
* **Production Validation:** Backend startup (`validate_production_config`) immediately aborts if `SECRET_KEY` is missing, insecure, or under 64 characters in production.
* **Diagnostic Redaction:** Configuration diagnostics report `CONFIGURATION VALID` or `CONFIGURATION INVALID` without exposing actual values.
* **Password Hashing (IMPLEMENTED - Phase 2):** Argon2id hashing via `argon2-cffi` (`time_cost=3`, `memory_cost=65536`, `parallelism=4`, `salt_len=16`). Constant-time password verification.
* **Token Architecture & Replay Detection (IMPLEMENTED - Phase 2):**
  * Short-lived JWT access tokens (15 minutes).
  * Long-lived refresh tokens (7 days) stored in database with unique JTI and Family ID.
  * Refresh token rotation: Every refresh invalidates the used refresh token and issues a new pair.
  * Replay attack detection: If an already-revoked refresh token is presented, the entire family of active sessions for that user is immediately revoked and audited.
  * Delivered via HTTP-only, `SameSite=Lax/Strict`, `Secure` cookies with client-side fallback.
* **Payment Security & Webhooks (IMPLEMENTED - Phase 2):**
  * Zero-trust pricing: Price is calculated strictly on the server (`extra='forbid'` rejects client amounts).
  * Non-custodial: No card, banking, or UPI PIN credentials ever stored.
  * PhonePe SHA256 checksum generation and constant-time webhook signature verification (`hmac.compare_digest`).
  * Idempotent entitlement activation with duration extensions.
  * IDOR protection preventing cross-user access to payment orders.

---

## 4. HTTP & Transport Security Controls (Phase 1 Implemented)

### Security Headers
Every HTTP response is fortified with defensive headers via `SecurityHeadersMiddleware`:
* `X-Content-Type-Options: nosniff` (Prevents MIME-sniffing)
* `X-Frame-Options: DENY` (Mitigates clickjacking)
* `Referrer-Policy: strict-origin-when-cross-origin` (Redacts sensitive URL parameters across origins)
* `Permissions-Policy: geolocation=(), microphone=(), camera=()` (Disables unnecessary browser device APIs)
* `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';`
* `Strict-Transport-Security: max-age=31536000; includeSubDomains` (Enforced in production HTTPS environments)

### CORS Policy
* Wildcard `*` origins are strictly prohibited in production.
* Configured via environment variable `CORS_ORIGINS` with explicit protocol and port.

### Request Size & Payload Protection
* `RequestSizeLimitMiddleware` checks incoming `Content-Length` headers against `MAX_REQUEST_SIZE_BYTES` (default 10 MB).
* Requests exceeding the threshold are aborted immediately with HTTP 413 `PAYLOAD_TOO_LARGE`.

---

## 5. Traceability & Request Correlation

* `RequestCorrelationMiddleware` guarantees every incoming request receives an `X-Request-ID`.
* Client-supplied IDs are validated against `^[a-zA-Z0-9_\-]{1,64}$` to prevent HTTP response splitting and header injection. Malformed headers are sanitized to a secure UUID4.
* The request ID is attached to:
  * Outgoing HTTP response headers (`X-Request-ID`).
  * Structured JSON application log records.
  * Standardized API error payloads.

---

## 6. Information Leakage Prevention

* Global error handlers catch all exceptions (`HTTPException`, `RequestValidationError`, unhandled `Exception`).
* Responses to clients never include:
  * Python tracebacks or file paths.
  * Database connection strings or internal SQL queries.
  * Environment variables or internal hostnames.
* Structured logging automatically redacts sensitive dictionary keys (`password`, `token`, `secret`, `authorization`, `cookie`, `key`).

---

## 7. Content Security & Integrity Controls (IMPLEMENTED - Phase 3)

### Hidden Test Case Isolation Invariant
* **Threat Model:** Students or automated grading-bypass tools attempting to scrape hidden evaluation test cases to hardcode expected outputs.
* **Invariant:** Database test cases with `is_hidden = True` and `is_sample = False` are strictly isolated server-side.
* **Enforcement:** Student endpoints (`/api/v1/problems/{slug}`) filter queries exclusively for `is_sample == True` and `is_hidden == False`. Hidden test cases are never serialized in student API responses.

### Structured Pedagogical Content (XSS Prevention)
* **Threat Model:** Stored Cross-Site Scripting (XSS) via rich text injection or raw HTML in educational content and explanations.
* **Invariant:** Lesson content blocks are strictly validated as structured JSON (headings, paragraphs, code, callout blocks).
* **Enforcement:** The frontend parses typed JSON blocks and renders native React DOM elements (`<h3>`, `<p>`, `<pre><code>`) without raw HTML decoding or `dangerouslySetInnerHTML`.

### Content Lifecycle & Public Exposure
* **Threat Model:** Premature leakage of draft problems, unreviewed contest questions, or retracted curriculum content.
* **Invariant:** Public student APIs strictly enforce `status == 'PUBLISHED'`.
* **Enforcement:** All draft, review, or archived content returns `HTTP 404 Not Found` to public users. Only verified `ADMIN` or `CONTENT_EDITOR` roles can view or author unpublished content via `/api/v1/admin/content/*`.

---

## 8. Phase 4 Security Controls: Progress, Submissions, Mistakes & Revision

### Zero-Execution Security Invariant
* **Threat Model:** Remote Code Execution (RCE), command injection, and container breakout via arbitrary student code execution.
* **Invariant:** Student code is strictly stored as untrusted text and queued (`QUEUED_FOR_FUTURE_JUDGE`). No in-process execution (`eval`, `exec`, `subprocess`) is executed in Phase 4.
* **Enforcement:** Code is stored directly to PostgreSQL without being invoked. No fake "Accepted" execution verdicts are fabricated.

### Strict Ingestion & Payload Protection
* **Payload Bound:** Maximum 64 KB (65,536 UTF-8 bytes). Enforced at Pydantic schema validation (`extra="forbid"`) and frontend input handlers.
* **Language Allowlist:** Restricted to `python`, `javascript`, `typescript`, `java`, `cpp`. Arbitrary values trigger HTTP 422.
* **Log Privacy:** Raw student code is excluded from application logger outputs and audit log metadata JSON.

### IDOR & Ownership Protection
* **Threat Model:** Malicious user inspecting, updating, or deleting another student's submissions, progress records, or mistake notes.
* **Invariant:** Every progress query, submission fetch, mistake mutation, and revision review filters strictly by `user_id == current_user.id`.
* **Enforcement:** Attempting to access an ID belonging to another user returns `HTTP 404 Not Found` (preventing ID enumeration).

---

## 9. Phase 5 Security Controls: Online Judge & Sandbox Execution

### Zero-Trust Isolation Architecture
* **Container Hardening:** Every execution occurs in an ephemeral Docker container with:
  - Network isolation: `--network none` (no egress or ingress)
  - Dropped Linux capabilities: `cap_drop: ["ALL"]`
  - Unprivileged user: `uid 10001:10001` (`judge:judge`)
  - Read-only root filesystem: `--read-only` with memory-backed tmpfs (`/tmp`, `/workspace`)
  - No privilege escalation: `no-new-privileges: true`
* **Resource Limits:**
  - Memory: `mem_limit` and `memswap_limit` (swap disabled)
  - CPU: `nano_cpus=1.0` (1 core)
  - Process limits: `pids_limit: 64` (fork-bomb prevention)
  - Wall-clock timeout: hard process kill on execution timeout
* **Hidden Test Case Privacy:**
  - Hidden test inputs and outputs are never included in API responses.
* **IDOR Defense:**
  - `GET /api/v1/submissions/{id}/result` and `POST /api/v1/submissions/{id}/cancel` strictly check user ownership (`submission.user_id == current_user.id`).
* **Anti-Fabrication Guarantee:**
  - If Docker daemon is absent on the host environment, the system reports `SANDBOX EXECUTION: NOT VERIFIED`. Live execution is never faked.

---

## 10. Future Security Controls (Phases 6–27)

| Security Subsystem | Target Phase | Implementation Strategy |
| :--- | :--- | :--- |
| **AI Prompt Injection Defense** | Phase 8 | Strict Pydantic output schemas, prompt guardrails, and token-bucket rate limits. |
| **Ephemeral SQL Sandbox** | Phase 20 | In-memory temporary SQLite instances for student SQL queries; complete network and filesystem isolation. |
| **File Upload Sanitation** | Phase 21 | Generated UUID filenames, strict MIME magic-number checking, virus scanning, and path traversal normalization. |

