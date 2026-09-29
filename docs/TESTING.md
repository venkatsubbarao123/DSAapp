# DSAapp Testing Strategy & Verification Guide

## 1. Testing Philosophy
* **Never assume; verify.** No feature is marked complete without automated tests.
* **Hermetic environments:** Tests use in-memory SQLite and isolated mock adapters to guarantee reproducibility.
* **Security verification:** Explicit security regression tests for headers, CORS, request IDs, size caps, and error isolation.

---

## 2. Running Backend Tests

Run the complete backend test suite using `pytest`:

```bash
# From workspace root
.\backend\.venv\Scripts\pytest -v

# Or from backend directory
cd backend
pytest -v
```

### Backend Test Coverage Breakdown:
1. `backend/tests/test_config.py`:
   - Validates that development configurations produce valid diagnostics without leaking secrets.
   - Asserts that production mode immediately rejects insecure secrets, SQLite URLs, and wildcard CORS.
   - Tests that valid production configs pass without errors.
2. `backend/tests/test_health.py`:
   - Validates `GET /health` root health endpoint and JSON envelope.
   - Validates `GET /api/v1/health` versioned health route.
   - Asserts that accessing undefined endpoints returns standardized 404 error envelopes with `request_id`.
3. `backend/tests/test_middleware_and_security.py`:
   - Verifies defensive HTTP headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`).
   - Verifies `X-Request-ID` propagation and client ID preservation.
   - Tests sanitization and replacement of malicious/header-injected request IDs.
   - Verifies CORS origin allowlisting (trusted allowed, untrusted blocked).
   - Verifies rejection of oversized payloads (HTTP 413).
   - Tests that internal server exceptions return generic 500 responses without leaking tracebacks, paths, or connection strings.
   - Verifies that root `.gitignore` protects `.env` files and certificates.

---

## 3. Running Frontend Tests

Run the Vitest test suite and static checks:

```bash
cd frontend

# Run unit and component tests
npm run test

# Run TypeScript static type check
npm run typecheck

# Run production build
npm run build
```

### Frontend Test Coverage Breakdown:
1. `src/test/App.test.tsx`:
   - Application shell and overview page rendering.
   - Routing transitions between `/` and `/status`.
   - 404 Not Found route rendering.
   - `ErrorBoundary` resilience test catching simulated component exceptions and displaying accessible recovery UI.
