# Operations Manual

> **Classification:** Operations — Standard  
> **Owner:** Platform Engineering  
> **Reviewed:** 2026-09-30

---

## Health Probes

All probes must return HTTP 200 in a healthy system.

| Endpoint | Type | Expected Response |
|----------|------|-------------------|
| `GET /liveness` | Process alive | `{"status": "alive"}` |
| `GET /readiness` | DB + Redis ready | `{"status": "ready", "database": "ok", "redis": "ok"}` |
| `GET /api/v1/health` | Extended health | `{"status": "healthy", ...}` |
| `GET /api/v1/health/live` | API-level liveness | `{"status": "alive"}` |
| `GET /api/v1/health/ready` | API-level readiness | `{"status": "ready"}` |

### Monitor health in a loop

```bash
watch -n 5 'curl -sf http://localhost:8000/readiness | python -m json.tool'
```

---

## Log Aggregation

### Application logs (structured JSON)

DSAapp emits structured JSON logs. In production, pipe to your log aggregator:

```bash
# docker-compose example — send to Loki or CloudWatch
docker-compose logs -f backend | jq .
```

### Key log fields

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 |
| `level` | `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| `event` | Human-readable message |
| `user_id` | Present on authenticated requests |
| `action` | Audit action (login, submit, etc.) |
| `ip` | Client IP |
| `path` | Request path |
| `status_code` | HTTP status |
| `duration_ms` | Request duration |

### Security audit log

Security events are written with `action` field. Query examples:

```bash
# All failed logins
docker logs dsaapp-backend | jq 'select(.action == "login_failed")'

# Admin actions
docker logs dsaapp-backend | jq 'select(.action | startswith("admin_"))'

# Payment events
docker logs dsaapp-backend | jq 'select(.action | startswith("payment_"))'
```

---

## Maintenance Procedures

### Database vacuuming (SQLite — dev only)

```bash
.\backend\.venv\Scripts\python.exe -c "
import sqlite3
conn = sqlite3.connect('dsaapp.db')
conn.execute('VACUUM')
conn.close()
print('Vacuum complete')
"
```

### Database backup (on-demand)

```bash
# Windows
.\backend\.venv\Scripts\python.exe scripts/backup_db.py --outdir backups

# Linux
python scripts/backup_db.py --outdir /var/backups/dsaapp
```

### Clear Redis cache

```bash
# Linux — connect to Redis container
docker-compose exec redis redis-cli FLUSHDB

# Python SDK
python -c "import redis; r=redis.Redis(); r.flushdb(); print('Flushed')"
```

> **Note:** Flushing Redis clears rate-limit counters and session caches. Users may need to log in again.

### Restart individual services

```bash
docker-compose -f docker-compose.prod.yml restart backend
docker-compose -f docker-compose.prod.yml restart redis
docker-compose -f docker-compose.prod.yml restart db
```

---

## Admin Panel Operations

Access the admin panel at: `https://yourdomain.com/admin`

### User management

| Action | API Endpoint |
|--------|-------------|
| Change user role | `PATCH /api/v1/admin/users/{id}/role` |
| Suspend/activate user | `PATCH /api/v1/admin/users/{id}/status` |
| View all users | `GET /api/v1/admin/users` |

### Judge health

| Action | API Endpoint |
|--------|-------------|
| Judge health | `GET /api/v1/admin/judge/health` |
| Judge queue | `GET /api/v1/admin/judge/queue` |

### System diagnostics

| Action | API Endpoint |
|--------|-------------|
| System diagnostics | `GET /api/v1/admin/system/diagnostics` |
| Audit log | `GET /api/v1/admin/system/audit` |

---

## Performance Monitoring

### Key metrics to watch

| Metric | Warning Threshold | Critical Threshold |
|--------|------------------|--------------------|
| API response time (p99) | > 500 ms | > 2000 ms |
| Database query time (p99) | > 200 ms | > 1000 ms |
| Judge execution time | > 10 s | > 30 s (timeout) |
| Redis latency | > 5 ms | > 50 ms |
| Error rate (5xx) | > 1% | > 5% |
| Memory usage (backend) | > 70% | > 90% |

### Database connection pool

Current settings (in `config.py`):

- `DATABASE_POOL_RECYCLE`: 1800 seconds (30 min)
- `DATABASE_POOL_TIMEOUT`: 30 seconds

Monitor pool exhaustion in logs: look for `QueuePool limit of size X overflow Y reached`.

---

## Cron Jobs (Production)

| Job | Schedule | Command |
|-----|----------|---------|
| Daily DB backup | `0 2 * * *` | `python scripts/backup_db.py --outdir /var/backups/dsaapp` |
| Backup cleanup (keep 30) | `0 3 * * *` | `find /var/backups/dsaapp -name "*.sqlite" -mtime +30 -delete` |
| Redis health check | `*/5 * * * *` | `redis-cli ping` (via monitoring agent) |

---

## Scaling Guidance

### Horizontal scaling (multiple backend replicas)

- Stateless: backend is horizontally scalable (all state in DB + Redis)
- Use a load balancer (nginx upstream / AWS ALB)
- Redis must be shared across all replicas (not per-process fallback)
- Database must use PostgreSQL (not SQLite) in multi-replica deployments

### Vertical scaling (single instance)

- Increase `DATABASE_POOL_RECYCLE` and `DATABASE_POOL_TIMEOUT` in config
- Increase uvicorn worker count: `--workers 4`
- Use PostgreSQL connection pooler (PgBouncer) at high load

---

## Security Operations

### Rotate secrets

1. Generate new `SECRET_KEY`: `openssl rand -hex 64`
2. Update `.env` on all instances
3. Restart backend (all active JWT tokens will be invalidated — users must re-login)
4. Rotate `PHONEPE_SALT_KEY` via PhonePe merchant portal — **UNVERIFIED — EXTERNAL ENVIRONMENT REQUIRED**

### Review audit logs for anomalies

```bash
# Top IP addresses by request count (last 24h)
docker logs dsaapp-backend --since 24h | jq -r '.ip' | sort | uniq -c | sort -rn | head -20

# All 403 Forbidden responses
docker logs dsaapp-backend | jq 'select(.status_code == 403)'
```
