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
# Run backend non-docker suite
.\backend\.venv\Scripts\pytest backend/tests -v --ignore=backend/tests/test_real_docker_integration.py

# Run backend real Docker sandbox integration suite (requires a running Docker daemon)
.\backend\.venv\Scripts\pytest backend/tests/test_real_docker_integration.py -v

# Run frontend Vitest suite
cd frontend
npm run test

# Run frontend TypeScript typecheck (0 errors)
npm run typecheck

# Build frontend production bundle
npm run build
```

### 5. End-to-End Acceptance Verification
With the backend running locally, this exercises the complete user journey
(register -> problems -> AI -> interview -> gamification -> logout) against the
live API:
```bash
python scripts/verify_production_acceptance.py
```

---

## Deployment

### Architecture

| Tier | Service | Notes |
| :--- | :--- | :--- |
| Frontend | Netlify / Vercel | Static SPA. `netlify.toml` and `vercel.json` both included. |
| Backend | Render / Fly.io / any Docker host | `backend/Dockerfile`, port `8000`. |
| Database | Neon PostgreSQL | Pooled connection string with `sslmode=require`. |
| Cache/Queue | Redis (optional) | Falls back to in-memory when `REDIS_REQUIRED=false`. |

### Required production environment variables (backend)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `ENVIRONMENT` | yes | Must be `production`. Startup aborts on invalid config. |
| `SECRET_KEY` | yes | Cryptographically random string, **64+ characters**. Used to sign JWTs. |
| `DATABASE_URL` | yes | Neon pooled URL, e.g. `postgresql://USER:PASS@ep-xxx.neon.tech/neondb?sslmode=require`. A sync `postgresql://` scheme is auto-upgraded to the async `postgresql+asyncpg` driver. |
| `CORS_ORIGINS` | yes | JSON list containing **only** the deployed frontend origin. Wildcards are rejected in production. |
| `ALLOWED_HOSTS` | yes | JSON list of accepted `Host` headers (backend domain). |
| `GOOGLE_AI_API_KEY` | yes | Gemini key for the AI Tutor. Server-side only — never sent to the browser. |
| `AI_PROVIDER` | yes | `gemini` for live AI. |
| `SECURE_COOKIES` | yes | Must be `true` in production (refresh-token cookie hardening). |
| `REDIS_URL` / `REDIS_REQUIRED` | no | Set `REDIS_REQUIRED=true` if the judge queue must use Redis. |
| `PHONEPE_*` | no | Only if enabling real payments (`PAYMENT_MODE=phonepe_production`). |

### Required production environment variable (frontend)

| Variable | Required | Description |
| :--- | :---: | :--- |
| `VITE_API_BASE_URL` | yes | Absolute origin of the deployed backend, e.g. `https://dsaapp-api.onrender.com`. Must be set at **build** time. |

### Deploying the frontend

```bash
cd frontend
VITE_API_BASE_URL=https://<your-backend-host> npm run build   # outputs dist/
```
Then connect the repository to Netlify or Vercel — both host configs are committed
(`netlify.toml`, `vercel.json`) and include the SPA history fallback plus the
security headers.

### Deploying the backend

`render.yaml` is committed and can be used as a Render Blueprint. It declares
`healthCheckPath: /health`, the Docker runtime and `./backend/Dockerfile`, and
every secret uses `sync: false` so nothing sensitive enters git.

```bash
docker build -t dsaapp-backend ./backend
docker run -p 8000:8000 --env-file .env.production dsaapp-backend
```

**Port binding.** The container CMD is:

```dockerfile
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1}"]
```

Shell form is required so `${PORT}` is expanded at runtime. A JSON `exec` array
cannot expand environment variables and therefore always binds port 8000 — which
is why a previous Render deployment bound `0.0.0.0:8000` while the platform
probed a different port and timed out. The `HEALTHCHECK` probe also follows
`$PORT`. Single worker by default, because every uvicorn worker runs the FastAPI
lifespan and would start its own judge worker loop.

**`ALLOWED_HOSTS` is mandatory in production.** `TrustedHostMiddleware` answers
`400 Bad Request` for any `Host` header it does not recognise. Render health-checks
the service through its generated hostname, so that hostname must be listed or
`/health` returns 400 and the service never goes LIVE. Wildcards are supported
(`*.onrender.com`). Startup now fails fast with an actionable message if the
list is empty.

`CORS_ORIGINS` and `ALLOWED_HOSTS` accept a JSON array, a comma-separated list, or
a single value — shell quoting differs between platforms and an unquoted value
must never crash startup.

### Render environment variables

| Variable | Required | Notes |
| :--- | :---: | :--- |
| `ENVIRONMENT` | yes | `production` |
| `SECRET_KEY` | yes | ≥ 64 chars. Startup **aborts** if shorter or prefixed `dev_`. |
| `DATABASE_URL` | yes | Neon pooled URL. Must not be SQLite. |
| `CORS_ORIGINS` | yes | Exact frontend origin only. No `*`. |
| `ALLOWED_HOSTS` | yes | Backend hostname(s), e.g. `*.onrender.com`. Omitting this makes `/health` return **400**. |
| `SECURE_COOKIES` | yes | `true` |
| `GOOGLE_AI_API_KEY` | yes | Server-side only. |
| `AI_PROVIDER` | yes | `gemini` |
| `JUDGE_ENABLED` | no | `false` on Render (no container runtime). |
| `ENABLE_API_DOCS` | no | `true` to expose `/docs` and `/openapi.json` in production. Off by default. |
| `WEB_CONCURRENCY` | no | Defaults to `1`. |

Apply migrations once against production before serving traffic:
```bash
python -m alembic -c alembic.ini upgrade head
```

> **Why the migration step matters.** At startup the API performs a *read-only*
> check of `alembic_version` against the revision this build expects
> (`EXPECTED_ALEMBIC_HEAD` in `backend/app/db/init_db.py`). It deliberately does
> **not** run `Base.metadata.create_all()` on PostgreSQL, because that emits a
> bare `CREATE TYPE ... AS ENUM(...)` for every model enum and fails with
> `duplicate key value violates unique constraint "pg_type_typname_nsp_index"`
> on any database Alembic has already provisioned. `create_all()` is retained
> only for SQLite (local dev and the throwaway in-memory test database).
>
> If you ever add a migration, bump `EXPECTED_ALEMBIC_HEAD` to the new revision
> id, otherwise startup logs a (non-fatal) schema-drift warning.

### Render deployment notes

Render does not provide a container runtime on standard web services, so the
online judge cannot execute code there. Two supported options:

| Option | What you get |
| :--- | :--- |
| **API only** (recommended for Render free/starter) | Set `JUDGE_ENABLED=false`. The API, auth, problems, progress, AI Tutor and interview all work. Submissions are queued but never executed. |
| **Dedicated judge host** | Deploy the backend to a Docker-capable host (Fly.io, a VPS, ECS) with `JUDGE_ENABLED=true` and `JUDGE_SANDBOX_DRIVER=docker`, then build the five judge images from `infra/judge/*`. |

Security is **not** weakened either way:
- `JUDGE_SANDBOX_DRIVER=mock` is rejected in production at startup — verdicts can never be fabricated.
- No untrusted code is ever executed inside the FastAPI process.
- If the Docker daemon is unreachable the judge fails **closed** with a safe error, never a fake "ACCEPTED".

### Running the whole stack with Docker Compose
```bash
cp .env.example .env     # then fill in SECRET_KEY / DATABASE_URL / GOOGLE_AI_API_KEY
docker compose up -d --build
```
The compose file starts an nginx gateway (`http://localhost`), the frontend, the
backend, PostgreSQL and Redis.

### Security checklist before going live
- [ ] `SECRET_KEY` is a fresh 64+ character random value (never the dev default).
- [ ] `.env` is **not** committed (it is already covered by `.gitignore`).
- [ ] `CORS_ORIGINS` lists only your real frontend origin.
- [ ] `GOOGLE_AI_API_KEY` lives only in the host's secret store.
- [ ] HTTPS is terminated in front of both tiers.
- [ ] Judge images (`infra/judge/*`) are built on a Docker-capable host; submissions
      require a working Docker daemon on the backend host.

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
