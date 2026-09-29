# Community Leaderboard Architecture & Privacy Specification

## 1. Executive Summary

The **DSAapp Leaderboard System** (`LeaderboardService` and `/api/v1/leaderboards`) provides community rankings across multiple competitive categories. Engineered for scale, fairness, and strict user privacy, rankings are computed directly from server transactions with deterministic tie-breaking, privacy-safe pseudonymization, and Redis caching.

---

## 2. Ranking Categories

| Category Code | Calculation Window | Score Metric |
| :--- | :--- | :--- |
| **`weekly_xp`** | Current ISO week (Monday 00:00 UTC to Sunday 23:59 UTC) | Sum of XP earned from `XPTransaction` |
| **`monthly_xp`** | Current calendar month (1st 00:00 UTC to end of month) | Sum of XP earned from `XPTransaction` |
| **`all_time_xp`** | Lifetime cumulative | `UserGamificationProfile.total_xp` |
| **`weekly_solves`** | Current ISO week | Distinct problems marked `SOLVED` in `UserProblemProgress` |
| **`streak`** | Active ongoing continuity | `UserGamificationProfile.current_streak` |

---

## 3. Deterministic Ranking & Tie-Breaking

To avoid ranking oscillation and non-deterministic sorting across paginated queries, all leaderboard queries enforce a secondary tie-breaker:

$$\text{Order By } \text{score DESC}, \text{user\_id ASC}$$

Ranks are computed sequentially ($1, 2, 3, \dots, N$) using standard 1-based indexing.

---

## 4. Privacy & Data Protection Safeguards

Leaderboards are public to the community, making privacy preservation paramount:

1. **Zero Email Leakage**:
   - Learner emails (`user.email`) are strictly barred from leaderboard API outputs.
2. **Display Name Pseudonymization**:
   - The system retrieves `UserProfile.display_name`.
   - If unset, the system generates a sanitized handle from the email prefix (`email.split("@")[0]`), never outputting the domain or full address.
3. **Identifier Masking**:
   - Only the public `user_id` is exposed to allow highlighting the current logged-in user.

---

## 5. Caching & Performance Architecture

Leaderboard calculations aggregate potentially large volumes of transactions. To ensure high throughput and low database load:

1. **Redis Cache-Aside Pattern**:
   - Key format: `leaderboard:{category}:{period_key}` (e.g. `leaderboard:weekly_xp:2026-W39`).
   - Cache TTL: **60 seconds**.
2. **Graceful Fallback**:
   - If Redis is unavailable or disconnected (e.g. in local development), queries fall back immediately to PostgreSQL/SQLite without service interruption.

---

## 6. Endpoints

- `GET /api/v1/leaderboards?category=weekly_xp&limit=20&offset=0`: Returns paginated community rankings.
- `GET /api/v1/leaderboards/me`: Returns the authenticated user's current ranking position, score, level, and streak across all 5 competitive categories in a single call.
