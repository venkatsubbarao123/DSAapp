# Advanced Gamification & Progression Architecture

## 1. System Philosophy

Gamification in DSAapp is strictly **server-authoritative**, **deterministic**, and **pedagogically aligned**. Every point of Experience (XP), level transition, streak increment, and achievement unlock is verified against immutable database state. Client requests attempting to submit arbitrary scores, spoof ratings, or claim duplicate rewards are blocked.

---

## 2. Integer Quadratic Level Progression

To eliminate floating-point rounding divergence and maintain predictable progression intervals across backend and frontend, levels follow an integer quadratic threshold curve:

$$XP(L) = 50 \times (L - 1) \times L$$

### Level Thresholds Table

| Level ($L$) | Cumulative XP Floor | Cumulative XP Ceiling | XP Required in Level |
| :---: | :---: | :---: | :---: |
| **1** | 0 | 100 | 100 |
| **2** | 100 | 300 | 200 |
| **3** | 300 | 600 | 300 |
| **4** | 600 | 1,000 | 400 |
| **5** | 1,000 | 1,500 | 500 |
| **10** | 4,500 | 5,500 | 1,000 |
| **20** | 19,000 | 21,000 | 2,000 |
| **50** | 122,500 | 127,500 | 5,000 |

### Mathematical Level Inversion
Given total XP $X$, the level is computed in $O(1)$ integer operations:

$$L = \left\lfloor \frac{1 + \sqrt{1 + 4 \times \frac{X}{50}}}{2} \right\rfloor$$

Implemented in [`LevelService.calculate_level()`](file:///c:/Users/venka/Downloads/DSAapp/backend/app/services/gamification/level_service.py).

---

## 3. Authoritative XP Reward Schedule

All awards are defined in `backend/app/services/gamification/xp_service.py`:

| Event Code | Base XP | Trigger Condition |
| :--- | :---: | :--- |
| `PROBLEM_SOLVE_EASY` | **10** | First accepted solution to an Easy problem |
| `PROBLEM_SOLVE_MEDIUM`| **25** | First accepted solution to a Medium problem |
| `PROBLEM_SOLVE_HARD` | **50** | First accepted solution to a Hard problem |
| `PROBLEM_SOLVE_EXPERT`| **100** | First accepted solution to an Expert problem |
| `DAILY_CHALLENGE` | **50** | Daily challenge solved on calendar date |
| `DAILY_FIRST_ATTEMPT` | **25** | Daily challenge solved on initial submission |
| `SESSION_COMPLETION` | **30** | Practice session completed |
| `ACCURACY_BONUS` | **20** | Practice session completed with accuracy $\ge 80\%$ |
| `STREAK_7_DAYS` | **100** | Streak reaches 7 consecutive calendar days |
| `STREAK_30_DAYS` | **500** | Streak reaches 30 consecutive calendar days |
| `REVISION_REVIEW` | **15** | Spaced repetition review completed |

---

## 4. Immutable XP Ledger & Idempotency

All XP modifications occur through append-only transactions in the `xp_transactions` table:

```sql
CREATE TABLE xp_transactions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    amount INTEGER NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    source_id VARCHAR(128),
    idempotency_key VARCHAR(128) UNIQUE NOT NULL,
    balance_after INTEGER NOT NULL,
    metadata_json JSON,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

### Idempotency Enforcement
The unique idempotency key is derived as:
$$\text{idempotency\_key} = \text{user\_id} : \text{event\_type} : \text{source\_id}$$

If duplicate requests occur (e.g. rapid double-clicking of "Claim Reward" or network retries), the database enforces the unique constraint, returning the existing transaction without inflating user XP.

---

## 5. Daily Streaks & Streak Freezes

1. **UTC Calendar Boundaries**:
   - Streaks are evaluated against UTC calendar days (`YYYY-MM-DD`).
2. **Same-Day Idempotency**:
   - Multiple solves on the same date maintain the active streak without incrementing it more than once.
3. **Consecutive Day Continuity**:
   - Activity on day $D$ following day $D-1$ increments `current_streak` by 1.
4. **Streak Freezes**:
   - If day $D-1$ is missed, but `streak_freeze_count > 0`, 1 freeze is atomically consumed to protect the streak.
   - If no freeze is available, `current_streak` resets to 1, while `longest_streak` is permanently preserved.

---

## 6. Skill Rating Progression

Skill rating starts at a baseline of **1,000** points and adjusts chronologically based on problem difficulty and drill performance:

| Activity | Rating Adjustment |
| :--- | :---: |
| Solve Easy Problem | **+5** |
| Solve Medium Problem | **+12** |
| Solve Hard Problem | **+25** |
| Solve Expert Problem | **+40** |
| Practice Drill ($\ge 80\%$ Accuracy) | **+10** |

All adjustments are recorded with reasons in `rating_history`.

---

## 7. Standard Achievements Catalog

The system evaluates 12 standard achievements across Bronze, Silver, Gold, and Platinum tiers:

| Code | Name | Tier | Criteria | XP Reward |
| :--- | :--- | :---: | :--- | :---: |
| `FIRST_SOLVE` | First Breakthrough | BRONZE | Solve 1 problem | 75 |
| `SOLVE_10` | Problem Solver | BRONZE | Solve 10 problems | 150 |
| `SOLVE_50` | Algorithm Centurion | SILVER | Solve 50 problems | 300 |
| `SOLVE_100` | Century Club | GOLD | Solve 100 problems | 600 |
| `STREAK_7` | Weekly Dedication | BRONZE | 7-day streak | 200 |
| `STREAK_30` | Monthly Mastery | SILVER | 30-day streak | 500 |
| `STREAK_100` | Unstoppable Force | GOLD | 100-day streak | 1,000 |
| `FIRST_HARD` | Summit Climber | SILVER | Solve 1 Hard problem | 250 |
| `PERFECT_SESSION` | Flawless Execution | BRONZE | 100% drill accuracy | 100 |
| `DAILY_CHAMP` | Daily Devotee | SILVER | Claim 7 daily challenges | 250 |
| `REVISION_HERO` | Memory Champion | BRONZE | Complete 10 revisions | 150 |
| `GRANDMASTER` | Algorithmic Grandmaster | PLATINUM | 1,500+ Skill Rating & 100 Solves | 2,000 |
