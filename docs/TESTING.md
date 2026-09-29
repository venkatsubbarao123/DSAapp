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

### Frontend Test Coverage Breakdown (22 tests):
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
5. `src/test/Progress.test.tsx` (6 tests):
   - Unauthenticated access guard redirecting to sign in prompt for `/progress`.
   - Authenticated `ProgressPage` with mathematical metrics, topic progress breakdown, and recent activity.
   - `SubmissionsPage` with zero-trust architectural execution notice and history list.
   - `MistakesPage` with categories, search input, and modal for recording errors.
   - `RevisionPage` with due items and recall quality actions (`AGAIN`, `HARD`, `GOOD`, `EASY`).
   - Solution code submission from `ProblemDetailPage` with 64KB size protection and queued non-execution notice.

---

## 5. Phase 5 Online Judge Tests

### Backend Test Coverage
1. **Output Comparator (`test_judge_comparator.py`)**:
   - Exact and normalized whitespace modes
   - CRLF and LF cross-platform handling
   - Trailing newline stripping
2. **Language Registry (`test_judge_languages.py`)**:
   - Supported runtimes (Python, C++, Java, Node.js, TypeScript)
   - Compile vs interpreted definitions
   - Dynamic command injection prevention
3. **Sandbox Isolation & Diagnostics (`test_judge_sandbox_and_security.py`)**:
   - Docker security spec (`--network none`, `--read-only`, `10001:10001`, `pids_limit: 64`, `cap_drop: ALL`)
   - Availability probing without exceptions
4. **Judge Worker & Lifecycle (`test_judge_worker_and_lifecycle.py`)**:
   - Verdict assignment (`ACCEPTED`, `WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `COMPILATION_ERROR`)
   - Invariant: `ACCEPTED` marks problem `SOLVED` and sets `solved_at`
   - Invariant: Non-accepted verdicts keep status `ATTEMPTED`
5. **API & IDOR Defense (`test_judge_api.py`)**:
   - Submission polling and result retrieval
   - IDOR protection on `/submissions/{id}/result`
   - User cancellation of queued jobs
   - Admin RBAC on `/admin/judge/health`

### Frontend Test Coverage (`src/test/Judge.test.tsx`)
1. **Verdict & Metrics Card**:
   - Renders Accepted verdict, test cases passed (`10 / 10`), runtime, and memory metrics.
2. **Safe Error Logs**:
   - Renders compiler and runtime error logs inside monospace `<pre>` blocks safely.

---

## 6. Phase 6 AI Learning System & Visualizers Tests

### Backend AI Test Coverage (`test_ai_api_and_recommendations.py`):
1. **AI Chat & Tutor Guidance**: Verifies conceptual tutoring without revealing full code implementations.
2. **Progressive Hint Disclosure**: Verifies 3-stage hint unlocking (`GENTLE`, `CONCEPTUAL`, `CONCRETE`).
3. **Complexity & Mistake Analysis**: Verifies error message classification and Big-O asymptotic analysis.
4. **Quota Gating**: Verifies 5 questions/day limit for Free tier and 50 questions/day for Pro tier.

### Frontend AI & Visualizers Test Coverage (`src/test/AiLearning.test.tsx`, `src/test/Visualizers.test.tsx`):
1. **AI Dashboard UI**: Quota progress bar, tutor tabs, and visualizer redirection.
2. **Visualizer Animation**: Frame-by-frame forward/backward stepping and category filtering.

---

## 7. Phase 7 Practice Engine & Gamification Tests

### Backend Test Coverage (22 tests across 7 test modules):
1. **Practice Engine (`test_practice_engine.py`)**:
   - Practice session creation and sequencing across modes.
   - Live accuracy calculation and problem outcome recording.
   - Strict IDOR defense on session reading and mutations.
   - Paginated historical session retrieval.
2. **XP Ledger & Progression (`test_gamification_xp_and_levels.py`)**:
   - Exact mathematical level curve verification ($XP(L) = 50 \times (L - 1) \times L$).
   - Atomic ledger entries with unique idempotency keys preventing replay exploits.
   - Profile retrieval and client XP manipulation rejection (`405 Method Not Allowed`).
3. **Streaks & Skill Rating (`test_gamification_streak_and_rating.py`)**:
   - Day-by-day streak transitions and same-day idempotency.
   - Atomic streak freeze consumption protecting continuity.
   - Rating adjustments scaled by problem difficulty (+5, +12, +25, +40) and accuracy bonus (+10).
4. **Daily Challenge (`test_daily_challenge.py`)**:
   - Deterministic SHA256 calendar date challenge selection.
   - Solution prerequisite verification, first-attempt bonus (+25 XP), and duplicate claim rejection.
5. **Achievements & Leaderboards (`test_achievements_and_leaderboard.py`)**:
   - 12 standard badges catalog and idempotent unlock evaluation.
   - Multi-category leaderboards with deterministic tie-breaking (`-score, user_id`).
   - Strict privacy preservation barring email leakage.
6. **Recommendations & Adaptive Difficulty (`test_recommendation_and_adaptive.py`)**:
   - Multi-factor candidate scoring and published/free content filtration.
   - Revision mode solved problem prioritization.
   - Dynamic difficulty calibration (step-up on 3 solves, step-down on 3 failures).
   - "Why recommended?" pedagogical explanation endpoint.
7. **Security & Anti-Cheat (`test_phase7_security_and_idor.py`)**:
   - Unauthenticated call rejections (HTTP 401).
   - Cross-user session IDOR attacks blocked (HTTP 403).
   - Pro tier practice mode gates enforced (`WEAK_AREA`, `MISTAKES`).
   - Direct XP, rating, and profile manipulation blocked.

### Frontend Practice & Gamification Test Coverage (`src/test/Practice.test.tsx`):
1. **Practice Dashboard**: Mode selection, problem count buttons, and drill initialization.
2. **Daily Challenge**: Problem card, XP reward breakdown, and claim state.
3. **Achievements**: Badge cards, tier filters, and unlocked status.
4. **Leaderboards**: Category switchers and privacy-safe ranking rows.
5. **Header Gamification**: Level, XP, streak pill, and `v0.7.0-phase7` tag.

---

## 8. Phase 8 Contests, Interview Mode, CP, SQL & OOP Tests

### Backend Test Coverage (25 tests across 5 test modules):
1. **Interactive SQL Engine (`test_sql_sandbox_and_engine.py` - 13 tests)**:
   - Sandbox execution with sample tables and multi-row datasets.
   - AST/lexical firewall rejecting `DROP`, `UPDATE`, `DELETE`, `INSERT`, `ALTER`, `CREATE`, `ATTACH`, `PRAGMA`.
   - Multi-statement `;` query rejection.
   - System catalog query rejection (`sqlite_master`, `sqlite_schema`).
   - Read-only enforcement (`SELECT` / `WITH ... SELECT` allowed).
   - Expected vs Actual result matrix equality verification.
   - Execution timeout enforcement (2.0s).
   - SQL problem retrieval and XP/streak rewards.
2. **AI Interview Simulation Mode (`test_interview_mode.py` - 3 tests)**:
   - 7 interview modes initialization and question retrieval.
   - Server-authoritative countdown timer calculation.
   - Question answer submission, AI evaluation report, and 5-dimensional rubric scoring.
3. **Competitive Programming & OOP Guides (`test_cp_and_oop.py` - 3 tests)**:
   - CP problem catalog by rating bands (Div 4 to Div 1).
   - Competitive rating history and global leaderboard.
   - OOP 4 pillars, SOLID refactoring diffs, and GoF patterns.
4. **Contest Arena Engine & Scoring (`test_contests_and_ranking.py` - 3 tests)**:
   - Contest lifecycle (`UPCOMING`, `LIVE`, `ENDED`) and server timer synchronization.
   - User registration flow and rejection of late join on ended contests.
   - Problem submission queuing, ICPC scoring/penalties, and anti-cheat 5s debounce.
5. **Security & IDOR Isolation (`test_phase8_security_and_idor.py` - 3 tests)**:
   - Contest submission rate-limiting enforcement.
   - Cross-user interview session IDOR protection.
   - Strict SQL sandbox isolation from application database.

### Frontend Test Coverage (`src/test/Phase8.test.tsx` - 7 tests):
1. **Phase 8 Navigation**: Verifies Header buttons for Contests, Interview, SQL, and OOP.
2. **ContestsPage**: Live, upcoming, and past contest tabs and registration badge.
3. **ContestDetailPage**: Problem matrix, countdown timer, submission panel, and live scoreboard.
4. **InterviewPage**: 7 interview track cards and customization configuration.
5. **CompetitivePage**: Rating profile widget, rating band filters, and global CP leaderboard.
6. **SqlPracticePage**: Schema inspector, AST firewall notice, and query execution.
7. **OopPage**: Four Pillars, SOLID principles with code diffs, and GoF patterns.

---

## 9. Phase 9 Test Coverage Breakdown: Admin, Analytics, Notifications & PWA

### Backend Test Coverage (23 tests):
1. **Admin RBAC & User Management (`test_admin_rbac_and_users.py` - 6 tests)**:
   - Superuser access verification (`403` for student/unauthenticated, `200` for admin).
   - User directory listing with search, role filters, status filters, and pagination.
   - User detail inspection including solve counts and activity stats.
   - Role elevation/demotion with mandatory audit reasons and audit log generation.
   - Self-demotion guardrail (`400 Bad Request` when admin attempts to demote own account).
   - Account status suspension/activation and self-suspension guardrail (`400 Bad Request`).
2. **Admin Content & Test Cases Studio (`test_admin_content_and_problems.py` - 4 tests)**:
   - Problem listing with test case counters and hidden test case counts.
   - Test case suite retrieval (`GET /api/v1/admin/problems/{id}/test-cases`).
   - Creation of public sample cases (`is_sample=True, is_hidden=False`) and hidden verification cases (`is_hidden=True`).
   - Test case deletion and verification case isolation from student curriculum endpoints.
3. **Admin Analytics & System Diagnostics (`test_admin_analytics_and_system.py` - 4 tests)**:
   - Authoritative overview KPIs derived strictly from live database aggregations.
   - Redis caching verification (subsequent requests served from cache).
   - Cache invalidation and bypass via `force_refresh=True`.
   - Real-time subsystem health diagnostics with zero secret leakage.
4. **Notifications & Broadcasts (`test_notifications_and_broadcasts.py` - 5 tests)**:
   - Notification creation, unread count badge increment, and list retrieval.
   - Notification mark-as-read and bulk mark-all-read.
   - Deduplication key enforcement blocking duplicate daily/streak alerts.
   - Notification channel preference matrix retrieval, mutation, and opt-out enforcement.
   - Multi-channel administrative broadcast dispatch (`POST /api/v1/notifications/broadcast`).
5. **Phase 9 Security & IDOR Isolation (`test_phase9_security_and_idor.py` - 4 tests)**:
   - Non-admin blocked from administrative routes (`403 Forbidden`).
   - Cross-user notification IDOR protection (cannot read or modify another user's notifications).
   - Cross-user notification preference IDOR protection.
   - Zero secret leakage validation across all admin diagnostic endpoints.

### Frontend Test Coverage (18 tests across 3 test files):
1. **Admin Console & Governance UI (`src/test/Phase9Admin.test.tsx` - 8 tests)**:
   - RBAC access gate rendering Access Denied and redirect for non-admin users.
   - AdminLayout sidebar rendering navigation links and superuser branding.
   - AdminOverviewPage rendering live KPIs and subsystem connectivity indicators.
   - AdminUsersPage rendering user directory and learner profile inspection modal.
   - AdminProblemsPage rendering catalog table and Test Cases Studio with hidden cases.
   - AdminSystemPage rendering health cards and Zero Secret Leakage Verification badge.
   - AdminAuditPage rendering security audit logs table with actor ID and action filters.
   - AdminBroadcastPage dispatching multi-channel announcements to active students.
2. **Notifications UI (`src/test/Phase9Notifications.test.tsx` - 3 tests)**:
   - NotificationBell rendering unread badge, polling for count, and toggling drawer.
   - NotificationsPage rendering notifications list with category tags and preferences link.
   - NotificationPreferencesPage rendering channel matrix toggles and save action.
3. **PWA & Offline Engine (`src/test/Phase9Pwa.test.tsx` - 7 tests)**:
   - Web App Manifest verification (`manifest.json` parameters, standalone display, shortcuts).
   - Service worker architecture verification (`sw.js` cache-first static assets, network-only sensitive bypass).
   - InstallPrompt component rendering banner and triggering install prompt.
   - InstallPrompt dismissing on close action.
   - PwaUpdateToast rendering update notification on service worker updatefound.
   - PwaUpdateToast applying skip-waiting update on click.

---

## 10. Current Cumulative Test Summary (Phases 1–9)

| Test Domain | Framework | Test File Count | Total Tests | Pass Rate |
|---|---|---|---|---|
| **Backend Unit, Integration & Security** | Pytest | 32 | 189 | **100% (189/189)** |
| **Backend Real Docker Sandbox Suite** | Pytest + Real Docker | 1 | 28 | **100% (28/28)** |
| **Total Backend Verification** | Pytest | 33 | 217 | **100% (217/217)** |
| **Frontend UI, Components & State**| Vitest | 13 | 61 | **100% (61/61)** |
| **Type Integrity** | TypeScript (`tsc --noEmit`) | — | Full Project | **0 errors** |
| **Production Build** | Vite (`npm run build`) | — | Full Project | **CLEAN** |

