# Deployment Guide

> **Classification:** Operations — Standard  
> **Owner:** Platform Engineering  
> **Reviewed:** 2026-09-30

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 20 GB SSD | 50 GB SSD |
| Docker | 24.x | 29.x |
| Docker Compose | 2.x | 2.x |
| Python | 3.13 | 3.13 |
| Node.js | 20 LTS | 20 LTS |

### External Services

| Service | Required | Notes |
|---------|----------|-------|
| PostgreSQL 16 | ✅ Yes | Can use docker-compose service |
| Redis 7 | ✅ Yes | Can use docker-compose service |
| PhonePe Payment Gateway | ⚠️ Production only | UNVERIFIED — EXTERNAL ENVIRONMENT REQUIRED |
| SMTP (email) | ⚠️ Optional | For notification emails |
| Docker Hub / Container Registry | ⚠️ For CI/CD | For image distribution |

---

## Environment Variables

Copy `.env.example` to `.env` and fill in all required values:

```bash
cp .env.example .env
```

### Required Variables

```env
# ── Security ──────────────────────────────────────────────────────────────────
SECRET_KEY=<generate: openssl rand -hex 64>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://dsaapp:<password>@db:5432/dsaapp
DATABASE_POOL_RECYCLE=1800
DATABASE_POOL_TIMEOUT=30

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0

# ── Payments (PhonePe) ─────────────────────────────────────────────────────────
# UNVERIFIED — EXTERNAL ENVIRONMENT REQUIRED
PHONEPE_MERCHANT_ID=<your-merchant-id>
PHONEPE_SALT_KEY=<your-salt-key>
PHONEPE_SALT_INDEX=1
PREMIUM_PRICE=99900

# ── Environment ────────────────────────────────────────────────────────────────
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourdomain.com

# ── AI Provider (optional) ─────────────────────────────────────────────────────
# Without this, AI endpoints use deterministic fallback mode
# GOOGLE_AI_API_KEY=<your-gemini-api-key>
```

---

## First Deployment

### 1. Clone and configure

```bash
git clone https://github.com/your-org/dsaapp.git /opt/dsaapp
cd /opt/dsaapp
cp .env.example .env
# Edit .env with production values
```

### 2. Build judge Docker images

```bash
docker build -t dsaapp-judge-python:latest infra/judge/python/
docker build -t dsaapp-judge-cpp:latest     infra/judge/cpp/
docker build -t dsaapp-judge-java:latest    infra/judge/java/
docker build -t dsaapp-judge-javascript:latest infra/judge/javascript/
```

### 3. Build the frontend

```bash
cd frontend
npm ci
npm run build
# Output: frontend/dist/
cd ..
```

### 4. Start infrastructure services

```bash
docker-compose -f docker-compose.prod.yml up -d db redis
# Wait for PostgreSQL to be ready (≈10 seconds)
docker-compose -f docker-compose.prod.yml exec db pg_isready -U dsaapp
```

### 5. Run database migrations

```bash
python -m alembic upgrade head
```

### 6. Start the application

```bash
docker-compose -f docker-compose.prod.yml up -d backend
```

### 7. Verify health

```bash
curl http://localhost:8000/liveness
# Expected: {"status": "alive"}

curl http://localhost:8000/readiness
# Expected: {"status": "ready", "database": "ok", "redis": "ok"}
```

### 8. Configure reverse proxy (nginx / caddy)

```nginx
# /etc/nginx/sites-available/dsaapp
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    root /opt/dsaapp/frontend/dist;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

> **Note:** TLS certificate provisioning via Let's Encrypt is  
> **UNVERIFIED — EXTERNAL ENVIRONMENT REQUIRED**. Run `certbot --nginx` after DNS is configured.

---

## Subsequent Deployments

```bash
cd /opt/dsaapp

# Pull latest code
git pull origin main

# Run migrations (if any)
python -m alembic upgrade head

# Rebuild frontend
cd frontend && npm ci && npm run build && cd ..

# Restart backend
docker-compose -f docker-compose.prod.yml up -d --force-recreate backend

# Verify
curl http://localhost:8000/readiness
```

---

## Backup Pre/Post Deployment

Always take a backup before deploying:

```bash
python scripts/backup_db.py --outdir /var/backups/dsaapp
```

---

## Production Checklist Before Go-Live

See `PRODUCTION_RELEASE_CHECKLIST.md` for the full checklist.
