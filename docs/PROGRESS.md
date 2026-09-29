# Learning Progress Tracking Architecture

## Overview
DSAapp implements a mathematical, server-authoritative progress tracking engine. User learning activity across lessons, problems, and curriculum tracks is tracked persistently with zero client-side trust.

---

## 1. Core Principles
1. **Mathematical Authority**: Progress percentages, completion counts, and mastery ratings are strictly calculated from persistent database rows—never from fabricated constants or unverified client assertions.
2. **Strict User Ownership**: All progress records (`UserLessonProgress`, `UserProblemProgress`) are keyed to `user_id`. No user can query or modify another user's progress records (IDOR immunity).
3. **State Machine Integrity**:
   - Lessons: `NOT_STARTED` → `IN_PROGRESS` → `COMPLETED`
   - Problems: `NOT_STARTED` → `ATTEMPTED` → `SOLVED`
4. **Non-Execution Invariant**: Submitting a solution marks a problem as `ATTEMPTED` (increments attempt counter and records timestamp), but **never** marks it `SOLVED` in Phase 4. `SOLVED` status is reserved for verified test-suite passage by the containerized judge (Phase 7).

---

## 2. Data Models & Constraints

### `UserLessonProgress`
- `id`: Primary key (`uuid_pkg.uuid4()`)
- `user_id`: Foreign key to `users.id` (Indexed, Cascade delete)
- `lesson_id`: Foreign key to `lessons.id` (Indexed, Cascade delete)
- `status`: Enum (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`)
- `completed_at`: Timestamp (UTC)
- `last_accessed_at`: Timestamp (UTC)
- **Unique Constraint**: `(user_id, lesson_id)` ensures exactly one tracking record per user per lesson.

### `UserProblemProgress`
- `id`: Primary key (`uuid_pkg.uuid4()`)
- `user_id`: Foreign key to `users.id` (Indexed, Cascade delete)
- `problem_id`: Foreign key to `problems.id` (Indexed, Cascade delete)
- `status`: Enum (`NOT_STARTED`, `ATTEMPTED`, `SOLVED`)
- `attempts_count`: Integer counter (default 0)
- `successful_attempts`: Integer counter (default 0)
- `first_attempted_at`: Timestamp (UTC)
- `last_attempted_at`: Timestamp (UTC)
- `solved_at`: Timestamp (UTC, nullable)
- `bookmarked`: Boolean flag
- `personal_difficulty`: Optional student rating
- **Unique Constraint**: `(user_id, problem_id)` ensures unique tracking per user per problem.

---

## 3. Aggregate Progress Computation

Progress is computed over **published** content only:
- **Lesson Completion Rate**:
  $$\text{Lesson \%} = \frac{\text{Completed Lessons}}{\text{Total Published Lessons}} \times 100$$
- **Problem Solving Rate**:
  $$\text{Problem \%} = \frac{\text{Solved Problems}}{\text{Total Published Problems}} \times 100$$
- **Overall Completion Rate**:
  $$\text{Overall \%} = \frac{\text{Completed Lessons} + \text{Solved Problems}}{\text{Total Published Lessons} + \text{Total Published Problems}} \times 100$$
- **Topic Level Calculations**: Computed dynamically per topic by aggregating subtopic lesson completions and child problem progress.

---

## 4. Mastery Insights (Premium Gated)
The endpoint `GET /api/v1/progress/insights/mastery` requires an active Premium entitlement (`require_premium`).
It calculates:
1. **Spaced Retention Score**: Aggregate score derived from average review ease factors.
2. **Active Study Streak**: Consecutive days with recorded progress or submission events.
3. **Mistake Breakdown**: Distribution of recorded mistakes grouped by cognitive category (`MistakeType`).
4. **Pattern Mastery**: Rating per algorithm pattern (e.g. `Two Pointers`, `Sliding Window`) based on problem attempts.
