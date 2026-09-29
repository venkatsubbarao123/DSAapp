# DSAapp — Multi-Channel Notification Engine

This document details the multi-channel notification architecture, event types, deduplication engine, delivery provider matrix, preference matrix, and broadcast dispatch systems implemented in **Phase 9**.

---

## 1. Notification Architecture

The DSAapp notification system operates as a unified event-driven communications layer supporting:
1. **In-App Notifications**: Real-time persisted notification items delivered to the user's topbar notification bell, unread badge counter, and dedicated Notification Center.
2. **Email Alerts**: Cryptographically compliant email messages dispatched via SMTP or development mock providers with template formatting and unsubscribe headers.

```
       [Platform Event Trigger]
        (Daily Drop, Streak Reminder,
        Contest Alert, Badge Unlock)
                   │
                   ▼
       [Deduplication Key Check]
      (Enforce 1 alert per event/day)
                   │
                   ▼
     [User Preferences Matrix Gate]
     (Check if In-App or Email is ON)
       ┌───────────┴───────────┐
       ▼                       ▼
  [IN-APP Channel]       [EMAIL Channel]
       │                       │
       ▼                       ▼
[Write to `notifications`   [Format Template & Send]
      Table]                   │
       │                       ▼
       │             [Record `notification_deliveries`]
       ▼                       │
[Update Unread Counter]        ▼
                         [Log Status (SENT/FAILED)]
```

---

## 2. Notification Event Types

| Event Type | Trigger Criteria | Default In-App | Default Email |
| :--- | :--- | :---: | :---: |
| **`DAILY_CHALLENGE`** | Midnight challenge published | `ON` | `OFF` |
| **`STREAK_REMINDER`** | Unbroken streak at risk (4 hours before UTC reset) | `ON` | `ON` |
| **`REVISION_DUE`** | Spaced repetition mistake due for consolidation | `ON` | `OFF` |
| **`CONTEST_STARTING`** | Rated contest starting in 15 minutes | `ON` | `ON` |
| **`ACHIEVEMENT_UNLOCKED`** | New badge or level milestone reached | `ON` | `OFF` |
| **`SYSTEM_NOTICE`** | Administrative broadcast or platform maintenance | `ON` | `ON` |

---

## 3. Deduplication Key Engine

To prevent notification spam caused by rapid worker retries, network hiccups, or multiple user triggers, every automated notification carries a deterministic `deduplication_key`:
- **Daily Challenge Key**: `daily_challenge:{problem_id}:{date}` (e.g. `daily_challenge:prob-42:2026-09-30`)
- **Streak Reminder Key**: `streak_reminder:{user_id}:{date}`
- **Revision Due Key**: `revision_due:{mistake_id}:{date}`
- **Contest Alert Key**: `contest_starting:{contest_id}:{user_id}`

### Enforced Invariant
If a notification with an identical `deduplication_key` and `user_id` already exists in the database, subsequent creation calls are safely short-circuited as idempotent no-ops, guaranteeing students never receive duplicate alerts for the same event.

---

## 4. User Preference Matrix & Enforced Opt-Out

Learners retain granular control over which communications they receive through the `/notifications/preferences` settings view:
- **Matrix Storage**: Stored in `notification_preferences` table with unique constraint on `(user_id, channel, notification_type)`.
- **System Notices Exception**: Critical security updates and mandatory service alerts (`SYSTEM_NOTICE`) bypass marketing opt-outs to ensure user security compliance.
- **Immediate Propagation**: Toggling a preference takes effect immediately on subsequent notification dispatches without application restart.

---

## 5. Administrative Broadcast Engine

Administrators can dispatch platform-wide announcements via `POST /api/v1/notifications/broadcast`:
- **Targeting Criteria**:
  - `target_role`: Broadcast to all users (`ALL`) or specific cohorts (`STUDENT`, `CONTENT_EDITOR`, `MODERATOR`).
  - `target_plan`: Target `FREE` or `PREMIUM` subscribers exclusively.
- **Multi-Channel Dispatch**: Deliver simultaneously to in-app notification drawers and registered email addresses.
- **Action URLs**: Supports linking announcements directly to contest arenas (`/contests/weekly-42`), practice sessions (`/practice`), or revision decks (`/revision`).
- **Audit Logging**: Every broadcast automatically generates a `BROADCAST_SENT` entry in the immutable `audit_logs` table recording the broadcast ID, target cohort, and total dispatched notifications.
