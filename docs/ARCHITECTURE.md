# DSAapp System Architecture

## Overview
DSAapp is an advanced, secure coding education and online judge platform built on a 20% Theory / 80% Practice pedagogical model.

---

## 1. System Topology & Request Flow

```
                      INTERNET
                         │
                         ▼
                  CDN / HTTPS Termination
                         │
                         ▼
                Reverse Proxy (Nginx)
                         │
         ┌───────────────┴───────────────┐
         ▼                               ▼
React 19 / TypeScript SPA         FastAPI API Gateway
   (Static Assets)                       │
                                         ▼
                            Request Correlation & Middlewares
                            (X-Request-ID, CORS, CSP, Size Limit)
                                         │
                                         ▼
                            Layered Backend Architecture
                            ├── Routers (/api/v1/*)
                            ├── Service Layer
                            ├── Repository Layer
                            └── Database Engine
                                         │
                   ┌─────────────────────┼─────────────────────┐
                   ▼                     ▼                     ▼
          PostgreSQL Database       Redis Broker          AI Gateway
          (Source of Truth)        (Cache & Queues)   (Provider Adapter)
                                         │                     │
                                         ▼                     ▼
                                   Worker Pools           LLM Providers
                                   (Celery / RQ)       (Strict Schema Validated)
                                         │
                                         ▼
                                   Sandbox Runners
                               (Isolated Container Pods)
```

---

## 2. Implementation Status by Component

| Subsystem | Status | Implementation Details |
| :--- | :--- | :--- |
| **API Gateway** | `IMPLEMENTED` | FastAPI with structured JSON logging, security middlewares, correlation IDs, and unified error envelopes. |
| **Health Probes** | `IMPLEMENTED` | `/health` and `/api/v1/health` verifying DB connection and Redis vitality. |
| **Database Architecture** | `OPERATIONAL` | SQLAlchemy 2.0 async engine + Alembic migrations. Full Phase 2 & 3 schemas: `users`, `user_profiles`, `refresh_tokens`, `payment_orders`, `payment_transactions`, `premium_entitlements`, `audit_logs`, `curricula`, `tracks`, `topics`, `subtopics`, `lessons`, `concepts`, `problems`, `problem_examples`, `hints`, `test_cases`, `tags`, `problem_patterns`. |
| **Authentication & RBAC** | `IMPLEMENTED` | Argon2id hashing, short-lived JWT access tokens, rotated refresh tokens with family reuse detection, HTTP-only SameSite cookies, RBAC dependencies (`require_role`, `require_admin`). |
| **Payments & Entitlements** | `IMPLEMENTED` | Server-authoritative pricing (₹999/yr), PhonePe gateway boundary with SHA256 checksums, constant-time signature verification, idempotent activation, `require_premium` gate. |
| **Curriculum & Content** | `IMPLEMENTED` | Hierarchical learning tree (Curriculum -> Track -> Topic -> Subtopic -> Lesson/Problem). Publishing workflow (`DRAFT`, `REVIEW`, `PUBLISHED`, `ARCHIVED`), server-enforced Free/Premium gating, hidden test case isolation, and XSS-immune structured lesson blocks. |
| **Cache & Rate Limiting** | `OPERATIONAL` | Redis sliding window rate limiter with in-memory local fallback. |
| **Frontend Foundation** | `OPERATIONAL` | React 19 + TypeScript + Vite. Dark-first tokens, ErrorBoundary, AuthContext (in-memory JWT + silent refresh), Curriculum views, Topics directory, Lessons reader, Problems directory with filters, Problem detail with sample cases & progressive hints, Pro upgrade flow. |
| **Online Judge Sandbox** | `PLANNED` | Phase 7: Isolated process runner (dev) and containerized sandboxes with network/memory/syscall constraints (prod). **FastAPI will never execute student code in-process.** |
| **AI System** | `PLANNED` | Phases 8–10: Backend AI provider adapter with strict Pydantic output validation and prompt defense barriers. |

---

## 3. Layered Backend Design

```
API Endpoints (/api/v1/*)
      │
      ▼  Pydantic v2 Request Validation & Schema Enforcement
Service Layer (Business Logic & Transactions)
      │
      ▼  Data Access Separation
Repository Layer (SQLAlchemy 2.0 Async Queries)
      │
      ▼
Database (PostgreSQL / SQLite)
```

* **No Business Logic in Routes:** Route handlers act strictly as controllers performing schema validation, dependency injection, and invoking services.
* **Database Independence:** Database queries are decoupled through async session management.

---

## 4. Execution Sandbox Architecture (Phase 7 Blueprint)

```
Student Code Submission
      │
      ▼
FastAPI (/api/v1/code/submit)
      │ Validates input size, syntax, language, and user authorization
      ▼
Submission Queue (Redis / BullMQ / Celery)
      │
      ▼
Isolated Worker Daemon
      │
      ▼
Containerized Sandbox Runner
  ├── Disabled Networking (--network none)
  ├── Hard CPU Quota (1 Core / 50% CPU)
  ├── Strict Memory Ceiling (256 MB)
  ├── Process / PID Cap (64 max)
  ├── Output Buffer Truncation (64 KB)
  ├── Execution Timeout (1.5s - 3.0s)
  └── Read-Only Root Filesystem + Ephemeral /tmp
      │
      ▼
Test Harness Evaluation (ACCEPTED, WRONG_ANSWER, TIME_LIMIT, RUNTIME_ERROR)
      │
      ▼
Database Submission Record
```

---

## 7. Phase 4 Architecture: Progress, Submissions, Mistakes & Revision
Phase 4 introduces zero-trust student learning persistence:
- **Progress Tracking Engine**: Mathematical, non-fabricated metrics for lessons and problems. `UserLessonProgress` and `UserProblemProgress` state transitions are strictly server-computed.
- **Untrusted Source Code Ingestion**: 64KB UTF-8 payload boundary, language allowlist (`python`, `javascript`, `typescript`, `java`, `cpp`), idempotency key deduplication. Code is stored safely without evaluation (`QUEUED_FOR_FUTURE_JUDGE`).
- **Mistake Notebook**: Structured cognitive error taxonomy (`CONCEPT_GAP`, `LOGIC_ERROR`, `EDGE_CASE`, `COMPLEXITY_ISSUE`, etc.) with user isolation and keyword search.
- **Spaced Revision System**: SM-2 inspired memory recall scheduling (`AGAIN`, `HARD`, `GOOD`, `EASY` outcomes) calculating dynamic intervals and ease factors.
- **Mastery Analytics**: Pro-entitlement gated server analytics computed over user attempt and review distributions.

## 8. Phase 5 Architecture: Online Judge & Code Execution
Phase 5 establishes the asynchronous online judge and container sandbox execution system:
- **Judge Queue**: Durable `JudgeJob` database queue with atomic claims, worker heartbeats, and dead job reclamation.
- **Judge Worker**: Background runner process executing compilation and test cases against visible and hidden inputs.
- **Container Sandbox**: Docker sandbox driver with zero network access (`--network none`), read-only rootfs, non-root user `uid 10001`, dropped capabilities (`cap_drop: ALL`), and memory/CPU/PIDs limits.
- **Output Comparator**: Whitespace and line-break normalization (`exact` and `normalized` modes).
- **Progress Integration**: `ACCEPTED` verdicts advance problem progress to `SOLVED` with `solved_at` timestamps.
- **Submissions & Admin API**: IDOR-protected result polling (`/submissions/{id}/result`), cancellation (`/submissions/{id}/cancel`), and administrative health monitoring (`/admin/judge/health`, `/admin/judge/queue`).

## 9. Phase 6 Architecture: AI Learning System & DSA Visualizers
Phase 6 establishes the AI-assisted pedagogical guidance and algorithm visualizer engine:
- **AI Tutor Service**: Multi-turn contextual guidance with strict anti-solution guardrails (never gives away raw solutions).
- **Progressive Hint Engine**: 3-tier staged hints (Gentle -> Conceptual -> Concrete).
- **Mistake & Complexity Analysis**: Automated classification of error output and Big-O asymptotic analysis.
- **Quota & Tier Enforcement**: 5 questions/day for Free learners, 50 questions/day for Pro subscribers.
- **Interactive Visualizers**: Frame-by-frame step execution for Binary Search, Two Pointers, Sliding Window, Bubble/Selection Sort, Linked Lists, Binary Trees, and BFS/DFS.

## 10. Phase 7 Architecture: Practice Engine & Advanced Gamification
Phase 7 establishes the server-authoritative practice drills, anti-cheat gamification, and competitive community leaderboards:
- **Practice Engine**: 8 targeted pedagogical modes (`QUICK`, `TOPIC`, `PATTERN`, `DIFFICULTY`, `WEAK_AREA`, `MISTAKES`, `REVISION`, `DAILY_CHALLENGE`) with live duration, accuracy tracking, and IDOR protection.
- **Integer Quadratic Level Curve**: $XP(L) = 50 \times (L - 1) \times L$ with $O(1)$ integer inversion preventing floating-point calculation drift.
- **Immutable XP Ledger**: Append-only `xp_transactions` table with composite idempotency key (`user_id:event_type:source_id`) preventing duplicate reward exploits.
- **Timezone-Aware Streaks**: UTC calendar day evaluation, same-day idempotency, streak freeze consumption, and milestone bonuses.
- **Skill Rating System**: Starting at 1,000 points with difficulty-scaled deltas (+5 Easy, +12 Medium, +25 Hard, +40 Expert) and drill accuracy bonuses.
- **Intelligent Recommendation Engine**: Multi-factor scoring ($TopicNeed + PatternNeed + RevisionPriority + MistakePriority + DifficultyFit$) filtering unpublished and inaccessible content.
- **Adaptive Difficulty**: Real-time calibration analyzing recent submissions (stepping up after 3 solves, stepping down after 3 failures).
- **Community Leaderboards**: Rankings across 5 categories (`weekly_xp`, `monthly_xp`, `all_time_xp`, `weekly_solves`, `streak`) with deterministic tie-breaking, privacy-safe display names, and Redis caching (60s TTL).

## 11. Phase 8 Architecture: Contests, Interview Mode, CP, SQL & OOP
Phase 8 incorporates real-time arena competitions, simulated technical interviews, rating ladders, isolated SQL execution, and system design patterns:
- **Contest Arena Engine**: Server-authoritative lifecycle state machine (`DRAFT`, `UPCOMING`, `LIVE`, `ENDED`, `ARCHIVED`) with UTC server synchronization. Strict ICPC scoring and penalty calculation with Redis standings caching. Anti-cheat heuristics enforce 5-second submission throttling and code similarity hashing.
- **AI Interview Simulation System**: 7 realistic interview tracks (`MOCK_TECHNICAL`, `COMPANY_FAANG`, `COMPANY_STARTUP`, `SPEED_DSA`, `SYSTEM_DESIGN`, `PAIR_PROGRAMMING`, `BEHAVIORAL`) evaluated against a calibrated 5-dimensional rubric (Problem Solving, Communication, Code Quality, Complexity, Architecture) with PromptGuard injection defense.
- **Competitive Programming (CP) Framework**: Problem catalog categorized by Codeforces rating bands (Div 4 [800–1199] to Div 1 [2000–2400+]) and an independent Elo-style competitive rating tracker with full historical auditing.
- **Interactive SQL Learning Sandbox**: Isolated, ephemeral in-memory SQLite sandbox with an AST/lexical firewall rejecting multiple statements, DDL, DML, `PRAGMA`, `ATTACH`, and SQLite catalog access. Result matrix equality verification and gamification XP integration.
- **OOP & Design Patterns Module**: In-depth coverage of the Four Pillars of OOP, SOLID design refactoring principles with before/after code diffs, and Gang-of-Four architectural patterns with multi-language implementations.

