# DSAapp — Advanced Secure Coding Education & Online Judge Platform

DSAapp is a production-grade, highly secure software engineering and data structures & algorithms platform engineered under a strict **20% Theory / 80% Practice** pedagogical model.

---

## Current Status: Phase 1 — Security & Architecture Foundation

| Layer / Feature | Phase 1 Status | Description |
| :--- | :--- | :--- |
| **API Gateway & Core** | `IMPLEMENTED` | FastAPI application with structured JSON logging, security headers, request correlation (`X-Request-ID`), size limit protection, and centralized error handling. |
| **Health Probes** | `IMPLEMENTED` | `/health` and `/api/v1/health` providing structured system vitality and connectivity metrics without leaking secrets. |
| **Database Abstraction** | `FOUNDATION ONLY` | SQLAlchemy 2.0 async engine supporting SQLite (dev/test) and PostgreSQL (prod) with dependency injection. Models planned for Phase 2 & 3. |
| **Cache / Queue Boundary** | `FOUNDATION ONLY` | `RedisService` interface supporting caching and queues with safe local development fallback. |
| **Frontend Foundation** | `FOUNDATION ONLY` | React 19 + TypeScript + Vite with dark-first design tokens, global `ErrorBoundary`, client routing, and system diagnostics page. |
| **Authentication & RBAC** | `PLANNED` | Phase 2: Argon2id password hashing, short-lived JWTs, token rotation, and server-side RBAC. |
| **Online Judge Sandbox** | `PLANNED` | Phase 7: Isolated execution sandbox. **FastAPI will never execute student code in-process.** |
| **AI Tutor & Solver** | `PLANNED` | Phases 8–10: Multi-lingual AI tutor and coach with strict schema validation. |

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
# Run backend pytest suite
.\backend\.venv\Scripts\pytest -v

# Run frontend test suite
cd frontend
npm run test
```

---

## Architectural Documentation
* [Architecture Blueprint](docs/ARCHITECTURE.md)
* [Security Specification & Compliance](docs/SECURITY.md)
* [Local Development Guide](docs/DEVELOPMENT.md)
* [Testing & Verification Guide](docs/TESTING.md)
* [Production Deployment & Infrastructure](docs/DEPLOYMENT.md)
* [Initial Implementation Gap Report](docs/IMPLEMENTATION_GAP_REPORT.md)
