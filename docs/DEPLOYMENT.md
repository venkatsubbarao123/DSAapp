# DSAapp Production Deployment & Infrastructure Specification

## 1. Production Architecture Overview

In production, DSAapp runs behind a reverse proxy / CDN with SSL/TLS termination:

```
Clients (HTTPS)
      │
      ▼
CDN / Edge Protection (Cloudflare / AWS CloudFront)
      │
      ▼
Reverse Proxy / Ingress (Nginx / Traefik / AWS ALB)
      ├── Terminates HTTPS
      ├── Enforces HTTP -> HTTPS redirect
      ├── Strips untrusted proxy headers
      └── Forwards X-Forwarded-For, X-Forwarded-Proto, Host
      │
      ├──> Frontend SPA (Static Nginx container on port 80)
      │
      └──> Backend API Gateway (Uvicorn / FastAPI container on port 8000)
```

---

## 2. Reverse Proxy & Header Forwarding Assumptions

When deploying behind an external load balancer or reverse proxy:
1. **Trusted Host Validation:**
   Configure `ALLOWED_HOSTS` in production to explicitly match your registered domain (e.g., `["dsaapp.com", "api.dsaapp.com"]`). The `TrustedHostMiddleware` will reject any request bearing a spoofed or unrecognized `Host` header.
2. **Forwarded Headers (`X-Forwarded-Proto` & `X-Forwarded-For`):**
   * Reverse proxies must set `proxy_set_header X-Forwarded-Proto https;`.
   * FastAPI uses forwarded protocol headers to verify secure cookie delivery.
3. **Cookie Security:**
   * Set `SECURE_COOKIES=true` and `SESSION_COOKIE_SECURE=true` in production to ensure cookies are marked `Secure` and `SameSite=Strict`.

---

## 3. Environment Validation Gate

The backend features an automated startup diagnostic gate (`Settings.validate_production_config()`):
* When `ENVIRONMENT=production`, startup will **fail immediately** if:
  * `SECRET_KEY` is missing, contains the `dev_` prefix, or has fewer than 64 characters.
  * `DATABASE_URL` contains `sqlite` instead of a production PostgreSQL connection string.
  * `CORS_ORIGINS` contains the wildcard `*` or is empty.
  * `SECURE_COOKIES` is set to `False`.

---

## 4. Container Deployment via Docker Compose

A complete production multi-container orchestration is provided in `docker-compose.yml`:

```bash
# 1. Provide validated production environment secrets
cp .env.example .env
# Edit .env with secure production credentials

# 2. Build and launch production containers
docker-compose up -d --build

# 3. Verify container health status
docker-compose ps
```

### Services Deployed:
* `dsaapp-gateway`: Nginx 1.27 reverse proxy (ports 80, 443).
* `dsaapp-frontend`: Static React build served via unprivileged Nginx (port 80).
* `dsaapp-backend`: Multi-worker FastAPI ASGI server running as unprivileged user `dsaapp` (UID 10001).
* `dsaapp-postgres`: PostgreSQL 16 database with health check probe.
* `dsaapp-redis`: Redis 7 in-memory cache and queue broker.

---

## 5. Execution Sandbox Deployment (Phase 7 Roadmap)

* **Host Requirement:** Production online judge execution requires a dedicated Docker/container daemon with cgroup v2 support to enforce process quotas, memory isolation, and network isolation (`--network none`).
* **Dual-Runner Architecture:**
  * **Production:** `ContainerizedSandboxRunner` using rootless containers.
  * **Development:** `IsolatedProcessRunner` with process-level restrictions when running without Docker.
