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

* **Secrets Storage:** All credentials (`SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, API keys) reside in environment variables. No secrets are committed to Git.
* **Production Validation:** Backend startup (`validate_production_config`) immediately aborts if `SECRET_KEY` is missing, insecure, or under 64 characters in production.
* **Diagnostic Redaction:** Configuration diagnostics report `CONFIGURATION VALID` or `CONFIGURATION INVALID` without exposing actual values.
* **Password Hashing (Phase 2):** Argon2id hashing via `argon2-cffi` with tuned memory and iteration costs. Plaintext passwords must never be logged, cached, or serialized.
* **Token Architecture (Phase 2):** Short-lived access tokens (15 minutes) with HTTP-only, `SameSite=Strict`, `Secure` refresh cookies and automatic token reuse revocation.

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

## 7. Future Security Controls (Phases 2–27)

| Security Subsystem | Target Phase | Implementation Strategy |
| :--- | :--- | :--- |
| **Server-Side RBAC & IDOR Defense** | Phase 2 | User ownership validation on all entity mutations; `STUDENT`, `CONTENT_EDITOR`, `MODERATOR`, `ADMIN` role gates. |
| **Rate Limiting** | Phase 2 | Sliding-window Redis token bucket on `/auth/*`, `/code/submit`, and `/ai/*`. |
| **Ephemeral SQL Sandbox** | Phase 20 | In-memory temporary SQLite instances for student SQL queries; complete network and filesystem isolation. |
| **File Upload Sanitation** | Phase 21 | Generated UUID filenames, strict MIME magic-number checking, virus scanning, and path traversal normalization. |
