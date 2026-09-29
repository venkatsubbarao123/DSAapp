# Disaster Recovery Playbook

> **Classification:** Operations — Critical  
> **Owner:** Platform Engineering  
> **Reviewed:** 2026-09-30

---

## Recovery Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **RPO** (Recovery Point Objective) | ≤ 24 hours | Daily automated backups |
| **RTO** (Recovery Time Objective) | ≤ 4 hours | Full restore from last verified backup |
| **MTTR** (Mean Time To Recovery) | ≤ 2 hours | Trained operator with runbook |

---

## Backup Architecture

### What is backed up

| Asset | Location | Frequency | Retention |
|-------|----------|-----------|-----------|
| Application database | `backups/<timestamp>-db.*` | Daily (or on-demand) | 30 days |
| Environment secrets | External secrets manager | N/A (out-of-band) | Indefinite |
| Docker images | Container registry | On every main-branch CI push | 10 versions |
| Application code | Git repository | On every commit | Indefinite |

### Backup manifest format

Each backup run produces a JSON manifest at `backups/<timestamp>-manifest.json`:

```json
{
  "timestamp": "2026-09-30T00:00:00Z",
  "db_type": "sqlite",
  "backup_path": "backups/2026-09-30T000000-db.sqlite",
  "sha256": "<hex>",
  "size_bytes": 1376256,
  "tables": 57
}
```

---

## Performing a Backup

### On-demand (development / pre-deployment)

```powershell
# Windows (dev)
.\backend\.venv\Scripts\python.exe scripts/backup_db.py --outdir backups

# Linux / production
python scripts/backup_db.py --outdir /var/backups/dsaapp
```

### Automated (cron / systemd)

Add to crontab (Linux) — daily at 02:00:

```cron
0 2 * * * cd /opt/dsaapp && python scripts/backup_db.py --outdir /var/backups/dsaapp >> /var/log/dsaapp-backup.log 2>&1
```

---

## Performing a Restore

### 1. Stop the application

```bash
docker-compose -f docker-compose.prod.yml down
```

### 2. Locate the target manifest

```bash
ls -lt /var/backups/dsaapp/*.json | head -5
```

### 3. Verify backup integrity before restoring

The restore script performs SHA-256 verification automatically.

```bash
python scripts/restore_db.py /var/backups/dsaapp/2026-09-30T000000-manifest.json \
    --target /opt/dsaapp/dsaapp.db
```

On success you will see:

```
[OK] SHA-256 verified
[OK] Integrity check passed (57 tables)
[OK] Database restored successfully
```

If the manifest or file is tampered with, the script exits with code 1 and prints:

```
[ERROR] SHA-256 mismatch — backup file may be corrupted or tampered
```

### 4. Run database migrations (if needed)

```bash
cd /opt/dsaapp
python -m alembic upgrade head
```

### 5. Restart the application

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 6. Validate health

```bash
curl -sf http://localhost:8000/readiness
curl -sf http://localhost:8000/api/v1/health/ready
```

Both must return HTTP 200 with `"status": "ready"`.

---

## Incident Response Playbook

### Severity Definitions

| Severity | Definition | Response Time |
|----------|-----------|---------------|
| P0 | Full production outage | 15 minutes |
| P1 | Core feature degraded | 1 hour |
| P2 | Non-critical feature affected | 4 hours |
| P3 | Minor issue / cosmetic | Next sprint |

### P0: Database corruption / data loss

1. **Declare incident** — notify on-call team.
2. **Stop writes** — set `MAINTENANCE_MODE=true` and redeploy.
3. **Assess scope** — determine last known-good backup from manifests.
4. **Restore** — follow "Performing a Restore" steps above.
5. **Verify** — run `pytest backend/tests/test_phase10_backup_restore.py -v`.
6. **Resume traffic** — remove maintenance mode.
7. **Post-mortem** — complete RCA within 48 hours.

### P0: Application crash (all instances down)

1. Check container logs: `docker-compose logs --tail=200 backend`
2. Check liveness probe: `curl http://localhost:8000/liveness`
3. Rollback to previous image: see `ROLLBACK.md`
4. If DB migration issue: `python -m alembic downgrade -1` then redeploy prior version.

### P1: Judge sandbox failure

1. Check Docker daemon: `systemctl status docker`
2. Test image: `docker run --rm dsaapp-judge-python:latest python3 -c "print('ok')"`
3. Re-build judge images: `docker-compose build judge-python judge-cpp judge-java judge-javascript`
4. If persistent, disable judge temporarily via admin panel, set `JUDGE_ENABLED=false`.

### P1: Redis failure

1. Redis failure triggers automatic in-memory fallback — application continues.
2. Rate limiting becomes per-process (not shared across replicas) — acceptable short-term.
3. Restart Redis: `docker-compose restart redis`
4. Monitor: `redis-cli ping`

---

## Contact & Escalation

| Role | Responsibility |
|------|---------------|
| On-Call Engineer | First responder, restore, escalation |
| Database Admin | Restore validation, data integrity |
| Security Officer | Breach assessment, disclosure |
| Engineering Lead | P0 coordination, post-mortem |

---

## Verification Matrix

Run after any restore to confirm full system health:

```bash
# Backend regression
.\backend\.venv\Scripts\pytest backend/tests/ --tb=short -q

# Health probes
curl http://localhost:8000/liveness
curl http://localhost:8000/readiness
curl http://localhost:8000/api/v1/health/ready

# Frontend build (verify no regressions)
cd frontend && npm run build
```

Expected: `232 passed` backend, `61 passed` frontend, both health probes 200.
