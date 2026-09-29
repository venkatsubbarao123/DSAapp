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

| Subsystem | Phase 1 Status | Target Implementation |
| :--- | :--- | :--- |
| **API Gateway** | `IMPLEMENTED` | FastAPI with structured JSON logging, security middlewares, correlation IDs, and unified error envelopes. |
| **Health Probes** | `IMPLEMENTED` | `/health` and `/api/v1/health` verifying DB connection and Redis vitality. |
| **Database Abstraction** | `FOUNDATION ONLY` | SQLAlchemy 2.0 with async SQLite (dev/test) and PostgreSQL pool configuration (prod). Full domain models planned for Phase 2 & 3. |
| **Cache & Queue Boundary** | `FOUNDATION ONLY` | `RedisService` abstraction with safe local dev fallback. Message queue processing planned for Phase 7. |
| **Frontend Shell** | `FOUNDATION ONLY` | React 19 + TypeScript + Vite with dark-first design tokens, global ErrorBoundary, client routing, and system diagnostics page. |
| **Authentication & RBAC** | `PLANNED` | Phase 2: Argon2id hashing, short-lived JWTs, refresh token family rotation, server-side RBAC guards. |
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
