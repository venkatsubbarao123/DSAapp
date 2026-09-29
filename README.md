# DSAapp — Advanced Secure Coding Education & Online Judge Platform

DSAapp is a production-grade, highly secure software engineering and data structures & algorithms platform engineered under a strict **20% Theory / 80% Practice** pedagogical model.

---

## Current Status: Phase 9 — Admin + Analytics + Notifications + PWA Verified

| Layer / Feature | Status | Description |
| :--- | :---: | :--- |
| **Foundation & Gateway** | `VERIFIED` | FastAPI gateway with correlation IDs, security headers, size limits, structured JSON logging, and health diagnostics. |
| **Auth & Entitlements** | `VERIFIED` | Argon2id password hashing, JWT access/refresh rotation, RBAC, Pro tier subscription boundary, and PhonePe payment integration. |
| **Curriculum & Content** | `VERIFIED` | Tracks, Topics, Subtopics, Lessons, Concepts, Problems, Test-Cases, Code Templates, and Admin/Editor authoring workflows. |
| **Progress & Spaced Repetition** | `VERIFIED` | Problem & lesson progress tracking, cognitive mistake classification, and Leitner/SM-2 spaced revision intervals. |
| **Online Judge & Sandbox** | `VERIFIED` | Multi-language compilation (Python, Java, C++, JS) executing in real Docker containers with cgroup resource limits and security isolation (28/28 tests passed). |
| **AI Tutor & Visualizers** | `VERIFIED` | Pedagogical multi-turn AI chat, progressive hint disclosure, complexity analysis, and interactive algorithm visualizers. |
| **Practice Engine** | `VERIFIED` | Multi-mode adaptive drills (`QUICK`, `TOPIC`, `PATTERN`, `DIFFICULTY`, `WEAK_AREA`, `MISTAKES`, `REVISION`), real-time accuracy, and IDOR protection. |
| **Server-Authoritative Gamification** | `VERIFIED` | Integer quadratic level curve $XP(L) = 50 \times (L - 1) \times L$, immutable ledger, UTC daily streaks, skill ratings, 12 mastery achievements, and privacy-safe leaderboards. |
| **Contest Arena Engine** | `VERIFIED` | Server-authoritative lifecycle, ICPC scoring/penalty rules, 5s throttle anti-cheat, code similarity detection, and Redis caching. |
| **AI Interview Simulator** | `VERIFIED` | 7 realistic interview tracks, authoritative countdown timers, 5-dimensional rubric scoring, and PromptGuard security. |
| **Competitive Programming** | `VERIFIED` | Rating bands (Div 4 to Div 1, 800-2400+), Codeforces catalog integration, and separate Elo-based competitive rating tracker. |
| **Interactive SQL Engine** | `VERIFIED` | Isolated ephemeral SQLite sandbox with AST/lexical firewall rejecting non-SELECT, system catalog, and chained queries. |
| **OOP & Design Patterns** | `VERIFIED` | Four Pillars of OOP, SOLID design refactoring principles with code diffs, and GoF patterns in Python, Java, C++, TypeScript. |
| **Admin & Governance Console** | `VERIFIED` | Fine-grained user directory, self-demotion/self-suspension guards, hidden test case studio, diagnostics, and append-only audit trail. |
| **Platform Analytics Engine** | `VERIFIED` | Authoritative database-driven KPIs, cross-subsystem metrics, zero-fabrication guarantees, and 60s Redis caching with force-refresh. |
| **Multi-Channel Notifications** | `VERIFIED` | In-app notification drawer with unread badge counter, transactional email, deduplication key engine, and preference matrix. |
| **Progressive Web App (PWA)** | `VERIFIED` | Web App Manifest, Cache-First static assets, strict Network-Only security bypass for sensitive endpoints, and offline shell fallback. |

---

## Quick Start

### 1. Environment Configuration
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1   # On Windows
pip install -r backend/requirements.txt
alembic -c backend/alembic.ini upgrade head
uvicorn backend.app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Running Automated Tests
```bash
# Run backend non-docker suite (217 tests)
.\backend\.venv\Scripts\pytest backend/tests -v --ignore=backend/tests/test_real_docker_integration.py

# Run backend real Docker sandbox integration suite (28 tests)
.\backend\.venv\Scripts\pytest backend/tests/test_real_docker_integration.py -v

# Run frontend Vitest suite (61 tests across 13 test files)
cd frontend
npm run test

# Run frontend TypeScript typecheck (0 errors)
npm run typecheck

# Build frontend production bundle
npm run build
```

---

## Architectural Documentation
* [Architecture Blueprint](docs/ARCHITECTURE.md)
* [Security Specification & Compliance](docs/SECURITY.md)
* [Local Development Guide](docs/DEVELOPMENT.md)
* [Testing & Verification Guide](docs/TESTING.md)
* [Administration Manual](docs/ADMIN.md)
* [Analytics Specification](docs/ANALYTICS.md)
* [Notifications Engine](docs/NOTIFICATIONS.md)
* [Progressive Web App (PWA)](docs/PWA.md)
* [Phase 8 Completion Report](docs/PHASE_8_COMPLETION_REPORT.md)
* [Phase 9 Completion Report](docs/PHASE_9_COMPLETION_REPORT.md)
