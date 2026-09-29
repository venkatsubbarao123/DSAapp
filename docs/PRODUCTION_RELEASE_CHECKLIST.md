# Production Release Checklist

> **Classification:** Operations — Critical  
> **Version:** Phase 10 Release Candidate  
> **Reviewed:** 2026-09-30

Complete every item before promoting to production. Mark each item ✅ when verified.

---

## 1. Test Suite Verification

| Check | Expected | Status |
|-------|----------|--------|
| Backend tests (all phases) | 232 / 232 PASS | ✅ VERIFIED 2026-09-30 |
| Frontend tests (Vitest) | 61 / 61 PASS | ✅ VERIFIED 2026-09-30 |
| TypeScript type check | 0 errors | ✅ VERIFIED 2026-09-30 |
| Production build (Vite) | Build succeeds | ✅ VERIFIED 2026-09-30 |
| Real Docker integration tests | 28 / 28 PASS | ✅ VERIFIED (Docker 29.8.1) |
| Phase 10 security audit | 10 / 10 PASS | ✅ VERIFIED 2026-09-30 |
| Phase 10 backup/restore | 2 / 2 PASS | ✅ VERIFIED 2026-09-30 |
| Health probe tests | 6 / 6 PASS | ✅ VERIFIED 2026-09-30 |

---

## 2. Database

| Check | Status |
|-------|--------|
| Alembic migration applied cleanly (`upgrade head`) | ☐ Verify in prod |
| Migration downgrade tested (`downgrade -1`) | ✅ Verified in dev |
| Migration re-upgrade tested | ✅ Verified in dev |
| Database backup taken pre-deployment | ☐ Perform before deploy |
| Backup SHA-256 verified | ☐ Confirm from manifest |
| 57 tables present post-restore | ☐ Verify if restore needed |

---

## 3. Security

| Check | Status |
|-------|--------|
| `SECRET_KEY` is ≥ 64 hex chars, randomly generated | ☐ Verify in prod `.env` |
| `SECRET_KEY` is NOT the dev default | ☐ Verify in prod `.env` |
| `PHONEPE_SALT_KEY` is production key (not test) | ☐ EXTERNAL — requires PhonePe portal |
| Admin self-demotion blocked | ✅ Verified by test |
| Admin self-suspension blocked | ✅ Verified by test |
| IDOR protection on user data | ✅ Verified by test |
| Docker sandbox: network=none | ✅ Verified by test |
| Docker sandbox: read-only rootfs | ✅ Verified by test |
| Docker sandbox: uid 10001:10001 | ✅ Verified by test |
| Docker sandbox: cap_drop ALL | ✅ Verified by test |
| Docker sandbox: pids_limit 64 | ✅ Verified by test |
| SQL sandbox: blocks DROP, DELETE, UPDATE, TRUNCATE | ✅ Verified by test |
| SQL sandbox: blocks INFORMATION_SCHEMA access | ✅ Verified by test |
| Payment: amount mass-assignment blocked | ✅ Verified by test |
| Payment: webhook signature validation | ✅ Verified by test |
| Security headers: X-Content-Type-Options | ✅ Verified by test |
| Security headers: X-Frame-Options | ✅ Verified by test |
| Security headers: Referrer-Policy | ✅ Verified by test |
| Security headers: Permissions-Policy | ✅ Verified by test |
| Security headers: Content-Security-Policy | ✅ Verified by test |
| Sensitive data redaction (password, tokens, keys) | ✅ Verified by test |
| Rate limiting active on auth endpoints | ✅ Implemented (Phases 1-2) |
| CORS restricted to `ALLOWED_ORIGINS` | ☐ Verify in prod `.env` |
| HTTPS enforced (HSTS header) | ☐ EXTERNAL — requires TLS setup |
| TLS certificate valid and auto-renewing | ☐ EXTERNAL — requires certbot |

---

## 4. Infrastructure

| Check | Status |
|-------|--------|
| PostgreSQL running and accepting connections | ☐ Verify in prod |
| Redis running and accepting connections | ☐ Verify in prod |
| Redis in-memory fallback tested | ✅ Verified by implementation |
| Judge Docker images built for all 4 languages | ☐ Build in prod |
| Judge image versions pinned (not `latest`) | ☐ Pin before release |
| DB connection pool configured (recycle=1800, timeout=30) | ✅ Implemented |
| Backup cron job scheduled | ☐ Set up on prod server |
| Log aggregation configured | ☐ Configure before launch |
| Monitoring/alerting configured | ☐ Configure before launch |

---

## 5. Application

| Check | Status |
|-------|--------|
| `/liveness` returns 200 `{"status": "alive"}` | ☐ Verify in prod |
| `/readiness` returns 200 `{"status": "ready"}` | ☐ Verify in prod |
| Frontend loads at root URL | ☐ Verify in prod |
| User registration flow works end-to-end | ☐ Smoke test in prod |
| Login / logout works | ☐ Smoke test in prod |
| Problem solve + judge verdict works | ☐ Smoke test in prod |
| AI tutor responds (or graceful fallback) | ☐ Smoke test in prod |
| Premium upgrade flow (dev mode) | ☐ Smoke test in prod |
| Admin panel accessible (admin user) | ☐ Smoke test in prod |

---

## 6. Documentation

| Document | Status |
|----------|--------|
| `docs/DEPLOYMENT.md` | ✅ Created |
| `docs/DISASTER_RECOVERY.md` | ✅ Created |
| `docs/ROLLBACK.md` | ✅ Created |
| `docs/OPERATIONS.md` | ✅ Created |
| `docs/PRODUCTION_RELEASE_CHECKLIST.md` | ✅ This document |
| `docs/PHASE_10_COMPLETION_REPORT.md` | ✅ Created |
| `.github/workflows/ci.yml` | ✅ Created |
| `README.md` | ✅ Existing |

---

## 7. CI/CD

| Check | Status |
|-------|--------|
| GitHub Actions workflow created | ✅ `.github/workflows/ci.yml` |
| CI passes on main branch | ☐ Verify after push |
| Docker image build stage in CI | ✅ Configured |
| Dependency security scan in CI | ✅ Configured |
| Release gate job blocks merge on failure | ✅ Configured |

---

## 8. Final Release Actions

- [ ] All items above marked ✅ (or ☐ items acknowledged as external)
- [ ] Final git commit with message `release: Phase 10 final production hardening and security audit`
- [ ] Git tag created: `git tag -a v1.0.0 -m "Phase 10 — Production Release Candidate"`
- [ ] Release notes communicated to stakeholders
- [ ] Rollback plan reviewed by on-call engineer
- [ ] Backup confirmed on production server before cutover

---

## External Environment Items (Cannot Be Verified Locally)

The following items require external infrastructure and are explicitly marked  
**UNVERIFIED — EXTERNAL ENVIRONMENT REQUIRED**:

1. **PhonePe live payment gateway** — Production `PHONEPE_MERCHANT_ID` and `PHONEPE_SALT_KEY` must be obtained from PhonePe merchant portal. Live webhook URL must be registered.
2. **TLS / HTTPS** — Production TLS certificate must be provisioned via Let's Encrypt or equivalent CA. HSTS header not active until HTTPS is configured.
3. **Remote PostgreSQL** — Production PostgreSQL must be provisioned and `DATABASE_URL` set. Migration must be run against production database.
4. **Live AI API** — `GOOGLE_AI_API_KEY` for Gemini must be obtained. Without it, AI endpoints run in deterministic fallback mode (no live responses).
5. **SMTP / email delivery** — Email notification delivery requires SMTP credentials.
6. **Container registry** — Production Docker images must be pushed to and pulled from a container registry.

Each of these items has documented reproduction steps in `DEPLOYMENT.md` or `OPERATIONS.md`.
