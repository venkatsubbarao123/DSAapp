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

### Backend Test Coverage Breakdown (49 tests):
1. `backend/tests/test_config.py` (3 tests):
   - Validates that development configurations produce valid diagnostics without leaking secrets.
   - Asserts that production mode immediately rejects insecure secrets, SQLite URLs, and wildcard CORS.
   - Tests that valid production configs pass without errors.
2. `backend/tests/test_health.py` (3 tests):
   - Validates `GET /health` root health endpoint and JSON envelope.
   - Validates `GET /api/v1/health` versioned health route.
   - Asserts that accessing undefined endpoints returns standardized 404 error envelopes with `request_id`.
3. `backend/tests/test_middleware_and_security.py` (8 tests):
   - Verifies defensive HTTP headers (`X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`).
   - Verifies `X-Request-ID` propagation and client ID preservation.
   - Tests sanitization and replacement of malicious/header-injected request IDs.
   - Verifies CORS origin allowlisting (trusted allowed, untrusted blocked).
   - Verifies rejection of oversized payloads (HTTP 413).
   - Tests that internal server exceptions return generic 500 responses without leaking tracebacks, paths, or connection strings.
   - Verifies that root `.gitignore` protects `.env` files and certificates.
4. `backend/tests/test_auth.py` (10 tests):
   - User registration with Argon2id password hashing and profile creation.
   - Duplicate email rejection and password complexity enforcement (zxcvbn).
   - Anti-mass-assignment defense blocking client role injection during registration.
   - User login, invalid credential rejection, and secure credential handling.
   - Refresh token rotation and replay-attack family revocation.
   - User profile retrieval `/api/v1/auth/me`.
   - Rate limiting on authentication routes (`/api/v1/auth/register`).
5. `backend/tests/test_authorization_and_rbac.py` (3 tests):
   - Role-based access control blocking student from admin endpoints (`403 Forbidden`).
   - Vertical privilege escalation prevention across user roles.
   - IDOR prevention ensuring users cannot query or manipulate others' payment orders.
6. `backend/tests/test_payments_and_premium.py` (4 tests):
   - Server-authoritative pricing (₹999/yr) rejecting client-submitted amounts.
   - End-to-end payment creation, verification, and idempotent premium entitlement activation.
   - Prevention of duplicate activation from replayed transactions.
   - PhonePe SHA256 checksum and constant-time webhook signature verification.
7. `backend/tests/test_content_models_and_db.py` (4 tests):
   - Idempotent seed routine populating curriculum, tracks, topics, lessons, and problems.
   - Relational integrity across pedagogical hierarchy (Curriculum -> Track -> Topic -> Subtopic -> Lesson/Problem).
   - Unique slug constraints across curricula, topics, lessons, and problems.
   - Many-to-many relationship mapping for problem tags and patterns.
8. `backend/tests/test_content_api.py` (7 tests):
   - Listing curricula and deep relationship retrieval.
   - Topic pagination, filtering, and subtopic drill-down.
   - Structured JSON lesson blocks retrieval.
   - Problem directory filtering by difficulty, pattern, tag, and search query.
   - **Hidden test case protection:** Invariant assertion that `is_hidden == True` test cases are never returned to student endpoints.
   - Draft and review status suppression: Unpublished content returns 404 to student clients.
9. `backend/tests/test_content_authorization_and_premium.py` (7 tests):
   - Free users denied access to Premium problems and lessons (`403 Forbidden`).
   - Premium users granted full access to Premium content.
   - Expired premium subscriptions denied access.
   - Role checks: Students forbidden from admin content management routes.
   - Content editor authoring and publishing lifecycle workflow.
   - Anti-mass-assignment protections on content authoring endpoints (`extra='forbid'`).
   - SQL injection resistance on search and filter parameters.

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

### Frontend Test Coverage Breakdown (16 tests):
1. `src/test/App.test.tsx` (4 tests):
   - Application shell and overview page rendering.
   - Navigation transitions between `/` and `/status`.
   - 404 Not Found route rendering.
   - `ErrorBoundary` resilience test catching simulated component exceptions and displaying accessible recovery UI.
2. `src/test/Auth.test.tsx` (4 tests):
   - Unauthenticated UI rendering (Sign In and Create Account buttons).
   - AuthModal toggle between login and registration modes.
   - Real-time client-side password strength meter during registration.
   - Successful login updating application state and storing in-memory token.
3. `src/test/PremiumPage.test.tsx` (3 tests):
   - Premium subscription page pricing cards and feature comparisons.
   - Unauthenticated upgrade click opening AuthModal.
   - Simulated development checkout flow with server verification.
4. `src/test/Content.test.tsx` (5 tests):
   - Structured Curriculum pathways rendering.
   - Problems directory with difficulty tags, search bar, and pattern badges.
   - Problem Detail view rendering problem statement, constraints, examples, sample test cases, and progressive hints.
   - Premium Content Gate rendering with upgrade CTA when Free user encounters locked problem.
   - Lesson Page rendering structured JSON blocks (headings, paragraphs, code) with zero XSS risk.
