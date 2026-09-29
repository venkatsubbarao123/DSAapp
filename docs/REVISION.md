# Spaced Repetition & Revision System Architecture

## Overview
DSAapp employs a spaced repetition engine inspired by the SuperMemo SM-2 algorithm to counteract the Ebbinghaus forgetting curve. It schedules timely reviews for complex problems, core algorithmic concepts, and previous student mistakes.

---

## 1. Revision Scheduling Algorithm

When a student performs a review action on a revision item, they grade their recall quality with one of four deterministic outcomes:

| Outcome | Recall Quality | Interval Multiplier | Ease Factor Adjustment |
|---|---|---|---|
| `AGAIN` | Failed recall; complete memory lapse | Reset to **1 day** | $-0.20$ (floor: 1.3) |
| `HARD` | Recalled with high effort | $\max(\text{interval} + 1, \text{interval} \times 1.2)$ | $-0.15$ (floor: 1.3) |
| `GOOD` | Successful recall with standard effort | $\max(\text{interval} + 1, \text{interval} \times \text{ease\_factor})$ | $+0.00$ |
| `EASY` | Instantaneous, effortless recall | $\max(\text{interval} + 2, \text{interval} \times \text{ease\_factor} \times 1.3)$ | $+0.15$ (cap: 3.5) |

### Minimum Invariants:
- Ease factor: Minimum 1.3, Maximum 3.5 (initial default: 2.5).
- Interval days: Always $\ge 1$.
- `due_at`: Calculated as `datetime.now(timezone.utc) + timedelta(days=interval_days)`.
- Overdue items: Evaluated where `due_at <= now()`.

---

## 2. Models: `RevisionItem` and `RevisionSchedule`

### `RevisionItem`
- `id`: Internal UUID
- `public_id`: Alphanumeric public ID (`rev_...`)
- `user_id`: Foreign key to `users.id` (Indexed)
- `source_type`: Enum (`LESSON`, `PROBLEM`, `MISTAKE`)
- `source_id`: Identifier referencing the source content
- `title`: Display title of the revision topic
- `priority`: Integer priority weight (1-10)
- `is_active`: Active tracking boolean

### `RevisionSchedule`
- `id`: Internal UUID
- `revision_item_id`: One-to-one foreign key to `revision_items.id` (Unique, Cascade delete)
- `due_at`: UTC timestamp for next review
- `last_reviewed_at`: UTC timestamp of latest review
- `review_count`: Total completed reviews counter
- `interval_days`: Current spacing interval
- `ease_factor`: Memorization difficulty coefficient (Float)
- `status`: Enum (`ACTIVE`, `COMPLETED`, `PAUSED`)

---

## 3. Review Queue API
- `GET /api/v1/revision/queue`: Returns all active items where `due_at <= now()`, ordered by priority descending and `due_at` ascending.
- `POST /api/v1/revision/items/{id}/review`: Accepts `{ outcome: "AGAIN" | "HARD" | "GOOD" | "EASY" }`, updates schedule parameters, and returns updated due timestamp.
