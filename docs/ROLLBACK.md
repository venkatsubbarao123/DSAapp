# Rollback Procedures

> **Classification:** Operations — Critical  
> **Owner:** Platform Engineering  
> **Reviewed:** 2026-09-30

---

## When to Roll Back

Roll back when:

- A deployment causes a regression in the test suite (backend 232 / frontend 61)
- Health probes fail after deployment (`/liveness` or `/readiness` return non-200)
- A database migration causes data corruption
- A security vulnerability is introduced

---

## Git Rollback

### Identify the target commit

```bash
git log --oneline -20
```

Each phase has a known-good tag:

| Phase | Commit | Description |
|-------|--------|-------------|
| Phase 9 complete | `29e9c16` | Admin + Analytics + Notifications + PWA |
| Phase 8 complete | (see git log) | Contests + Interview + CP + SQL + OOP |
| Phase 7 complete | `aa10bc0` | Practice + Gamification |
| Phase 6 complete | `cb8591f` | AI Learning + Visualizers |
| Phase 10 release | `HEAD` | Final production hardening |

### Rollback application code (no DB change)

```bash
# Create a revert commit (safe — preserves history)
git revert HEAD --no-edit

# OR: Hard reset to known-good commit (destructive — only on isolated branch)
git reset --hard <commit-hash>
git push --force-with-lease origin main
```

### Redeploy after code rollback

```bash
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --force-recreate
```

---

## Database Migration Rollback

### Roll back the last migration (one step)

```bash
cd /opt/dsaapp
python -m alembic downgrade -1
```

### Roll back to a specific revision

```bash
# List all revisions
python -m alembic history

# Downgrade to specific revision ID
python -m alembic downgrade <revision-id>
```

### Known migration chain

```
7c139d4e5f6a  ←  Phase 9 notification tables        HEAD
<prev>         ←  Phase 8 contest/interview tables
<prev>         ←  Phase 7 practice/gamification tables
<prev>         ←  Phase 6 AI + visualizer tables
<prev>         ←  Phase 5 judge tables
<prev>         ←  Phase 4 progress/submission tables
<prev>         ←  Phase 3 curriculum tables
<prev>         ←  Phase 1-2 user/auth tables
```

### Verify migration state

```bash
python -m alembic current
python -m alembic heads
```

---

## Docker Image Rollback

### Identify the previous image tag

```bash
docker images dsaapp-backend --format "table {{.Tag}}\t{{.CreatedAt}}" | head -10
```

### Roll back to previous image

```bash
# In docker-compose.prod.yml, pin the image tag:
# image: dsaapp-backend:<previous-sha>

docker-compose -f docker-compose.prod.yml up -d --force-recreate backend
```

### Roll back judge images

```bash
docker-compose -f docker-compose.prod.yml up -d --force-recreate \
  judge-python judge-cpp judge-java judge-javascript
```

---

## Post-Rollback Verification

After any rollback, run the full verification sequence:

```bash
# 1. Check health probes
curl -sf http://localhost:8000/liveness && echo "LIVENESS OK"
curl -sf http://localhost:8000/readiness && echo "READINESS OK"

# 2. Run backend regression (skip Docker judge if judge was rolled back)
.\backend\.venv\Scripts\pytest backend/tests/ \
  --ignore=backend/tests/test_real_docker_integration.py \
  -q --tb=short

# 3. Verify migration state
python -m alembic current

# 4. Verify frontend build
cd frontend && npm run build
```

---

## Emergency Contacts

| Scenario | Action |
|----------|--------|
| Cannot roll back migration | Restore from backup — see `DISASTER_RECOVERY.md` |
| Data loss during rollback | Stop all writes, engage DBA immediately |
| Security breach detected | See incident playbook in `DISASTER_RECOVERY.md` |
