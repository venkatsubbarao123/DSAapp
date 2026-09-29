# DSAapp — Platform Analytics & Metrics Engine

This document details the architectural design, mathematical calculation principles, Redis caching layer, and data integrity guarantees of the **Phase 9** Analytics subsystem.

---

## 1. Zero-Fabrication Principle & Architectural Foundation

The DSAapp analytics engine operates under an uncompromising **Zero-Fabrication Principle**:
- **No Mock or Synthetic Telemetry**: Active users, submission counts, acceptance rates, streak tiers, and revenue numbers are **never hardcoded or simulated**.
- **Live Database Aggregations**: All key performance indicators (KPIs) and breakdowns are computed via targeted SQL aggregation queries (`COUNT`, `SUM`, `AVG`, `GROUP BY`, date-window filters).
- **Graceful Zero-State Support**: On empty databases or fresh test environments, analytics return mathematically sound zeros (`0`, `0.0%`, `[]`) rather than fallback dummy numbers.

---

## 2. Analytics Subsystem Matrix

The analytics engine produces comprehensive multi-dimensional intelligence across seven core domains:

### A. Overview KPIs
- **`total_users`**: Total registered accounts in the system (`SELECT COUNT(id) FROM users`).
- **`active_users_dau`**: Daily Active Users who submitted code, completed lessons, or updated progress within the trailing 24 hours.
- **`active_users_mau`**: Monthly Active Users active within the trailing 30 days.
- **`total_problems`**: Count of published algorithmic problems in the curriculum.
- **`total_submissions`**: Total code evaluations dispatched through the online judge.
- **`total_accepted_submissions`**: Count of submissions with verdict `ACCEPTED`.
- **`platform_acceptance_rate`**:
  $$\text{Platform Acceptance Rate} = \left( \frac{\text{total\_accepted\_submissions}}{\text{total\_submissions}} \times 100 \right)$$
  (Defaults to `0.0` when total submissions equal 0).
- **`total_premium_subscribers`**: Count of users with active `PREMIUM` subscription entitlements.
- **`total_revenue_amount`**: Sum of completed monetary transactions (`SELECT COALESCE(SUM(amount), 0) FROM payment_orders WHERE status = 'COMPLETED'`).

### B. User Demographics & Roles
- Distribution of accounts across roles (`STUDENT`, `CONTENT_EDITOR`, `MODERATOR`, `ADMIN`).
- Subscription plan distribution (`FREE`, `PREMIUM`).
- Account verification status ratios (email verified vs unverified).

### C. Content & Submissions
- Breakdown of problems by difficulty tier (`EASY`, `MEDIUM`, `HARD`, `EXPERT`).
- Breakdown of submissions by judge verdict (`ACCEPTED`, `WRONG_ANSWER`, `TIME_LIMIT_EXCEEDED`, `MEMORY_LIMIT_EXCEEDED`, `COMPILATION_ERROR`, `RUNTIME_ERROR`, `OUTPUT_LIMIT_EXCEEDED`).
- Programming language usage distribution (Python, Java, C++, JavaScript).

### D. Gamification & Engagement
- XP distribution across learner cohorts.
- Streak distribution: Active streaks categorized into cohorts (0 days, 1–3 days, 4–7 days, 8–14 days, 15–30 days, 30+ days).
- Achievement badge unlock metrics.

### E. Contests & Interview Simulator
- Total rated contests hosted and average participant turnouts.
- Total mock interview sessions conducted across the 7 tracks (Big Tech SWE, Startup Fullstack, Systems Engineering, Fintech High Frequency, Machine Learning, Frontend Specialist, Junior Fundamentals).
- Average interview rubric ratings across Problem Solving, Communication, Code Quality, Edge Cases, and Complexity Analysis.

### F. Online Judge Performance
- Total jobs processed and queue throughput.
- P50, P90, and P99 evaluation latency percentiles in milliseconds.
- Current pending queue backlog and active worker heartbeats.

### G. Revenue & Subscriptions
- Completed order count, average order value (AOV), and gross transactional revenue.
- Time-series daily revenue trajectories.

---

## 3. High-Performance Redis Caching Layer

To guarantee sub-15ms response times on executive dashboard queries while avoiding repetitive table scans, analytics results are protected by an intelligent Redis caching architecture:

```
[Admin Request]
       │
       ▼
[Cache Check: admin:analytics:overview]
       ├── (Hit) ──> Return cached JSON response (< 5ms)
       │
       └── (Miss / Force Refresh)
              │
              ▼
       [Execute Optimized SQL Aggregations]
              │
              ▼
       [Write to Redis (TTL = 60s)]
              │
              ▼
       [Return Authoritative Response]
```

### Cache Invariants
- **Cache Key Namespace**: `admin:analytics:{domain}` (e.g. `admin:analytics:overview`, `admin:analytics:users`, `admin:analytics:judge`).
- **Time-to-Live (TTL)**: 60 seconds (`EX = 60`).
- **Force Refresh (`?force_refresh=true`)**: Administrative clients can explicitly bypass and refresh the cache during incident reviews or live broadcasts.
- **Graceful In-Memory Fallback**: When Redis is offline or degraded, the analytics service automatically falls back to live DB execution with zero application errors or downtime.
