# Practice Engine Architecture & Specification

## 1. Executive Summary

The **DSAapp Practice Engine** transforms passive algorithmic study into structured, targeted, and pedagogically sound training drills. Built upon a server-authoritative architecture, it orchestrates multi-problem sessions, sequences algorithmic challenges according to learner proficiency, computes real-time accuracy and duration metrics, and delivers anti-cheat gamified rewards upon drill completion.

---

## 2. Core Practice Modes

The Practice Engine implements 8 distinct pedagogical modes defined in `PracticeMode` (`backend/app/models/gamification.py`):

| Practice Mode | Tier Gate | Pedagogical Target & Behavior |
| :--- | :--- | :--- |
| **`QUICK`** | Free / All | Rapid 3-to-10 problem drill calibrated around the learner's skill rating. |
| **`TOPIC`** | Free / All | Deep focused immersion in a specific curriculum topic (e.g. Dynamic Programming, Trees). |
| **`PATTERN`** | Free / All | Targeted pattern mastery (e.g. Two Pointers, Sliding Window, Fast & Slow Pointers). |
| **`DIFFICULTY`** | Free / All | Specific challenge tier practice (Easy, Medium, Hard, Expert). |
| **`REVISION`** | Free / All | Spaced retention reviews prioritizing previously solved problems approaching cognitive decay. |
| **`WEAK_AREA`** | **PRO Only** | Cognitive gap targeting based on logged errors and low-accuracy topic clusters. |
| **`MISTAKES`** | **PRO Only** | Error reinforcement re-serving problems where runtime errors, WA, or TLE occurred. |
| **`DAILY_CHALLENGE`**| Free / All | Calendar-based deterministic problem with first-attempt bonus rewards. |

---

## 3. Session Lifecycle & State Machine

```
         ┌───────────────────┐
         │   Create Session  │
         │ (mode, target_cnt)│
         └─────────┬─────────┘
                   │
                   ▼
         ┌───────────────────┐
         │    IN_PROGRESS    │◄──────────────┐
         └─────────┬─────────┘               │
                   │                         │
            Record │ Result (Solve/Pass)     │ Next Problem
                   ▼                         │
         ┌───────────────────┐               │
         │  Session Problem  │───────────────┘
         │  Attempt Tracked  │
         └─────────┬─────────┘
                   │ All problems attempted
                   │ or user completes
                   ▼
         ┌───────────────────┐
         │     COMPLETED     │
         │  (Award XP/Rating)│
         └───────────────────┘
```

1. **Session Creation (`POST /api/v1/practice/sessions`)**:
   - Validates user tier entitlements (`WEAK_AREA` and `MISTAKES` strictly require active Pro subscription).
   - Intelligently queries candidate problems via `IntelligentProblemSelector`.
   - Persists `PracticeSession` and child `PracticeSessionProblem` records with deterministic sequence indices (`1, 2, ... N`).
2. **Problem Result Recording (`POST /api/v1/practice/sessions/{id}/problem/{pid}/result`)**:
   - Enforces user IDOR ownership (`session.user_id == current_user.id`).
   - Updates `attempted`, `solved`, and `time_spent_seconds`.
   - Recalculates live session accuracy: $\text{accuracy} = \frac{\text{solved\_count}}{\text{completed\_count}}$.
   - Immediately records problem solve in `UserProblemProgress` and advances streak if qualifying.
3. **Session Completion (`POST /api/v1/practice/sessions/{id}/complete`)**:
   - Calculates aggregate duration from problem timestamps.
   - Computes completion and accuracy bonuses.
   - Awards XP through the immutable `XPTransaction` ledger idempotently.
   - Updates skill rating and evaluates achievement milestones.
   - Marks status as `COMPLETED`.

---

## 4. Anti-Cheat & IDOR Security Guarantees

1. **Zero Client Authority**:
   - Clients never send XP amounts, scores, ratings, or level numbers.
   - All XP amounts are calculated by `XPService` using strict server rules.
2. **Strict Session Ownership (IDOR Defense)**:
   - Every read (`GET /sessions/{id}`) and mutation (`POST /problem/{pid}/result`, `POST /complete`) checks `session.user_id == current_user.id`.
   - Cross-user attempts are rejected with `HTTP 403 Forbidden` and audited.
3. **Ledger Idempotency**:
   - Every XP event has a unique composite key: `idempotency_key = f"{user_id}:{event_type}:{source_id}"`.
   - Repeated requests will not inflate learner XP balances.
