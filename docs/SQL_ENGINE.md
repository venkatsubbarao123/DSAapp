# DSAapp Interactive SQL Learning Sandbox & Engine

## Overview
Phase 8 introduces the **Interactive SQL Engine**, enabling hands-on practice with complex SQL queries (Aggregations, Window Functions, Multi-Table Joins, Subqueries) with absolute security and database isolation.

---

## 1. Security Architecture & Threat Isolation

### The Fundamental Rule
> **Arbitrary student SQL is NEVER executed against the application or production database.**

```
[Student SQL Input]
        │
        ▼
[Lexical & AST Firewall]  ──(Blocked keyword or multiple queries)──► [REJECTED (400)]
        │
        ▼ (Valid single SELECT query)
[Ephemeral In-Memory SQLite Instance]
   ├── Problem DDL loaded
   └── Problem Seed Rows populated
        │
        ▼
[Sandboxed Read-Only Execution with Timeout (2.0s)]
        │
        ├── Extract Column Names & Tuples
        └── Compare with Expected Output Table
        │
        ▼
[Destruction of In-Memory Database]
```

---

## 2. AST & Lexical Firewall Rules
Before any query reaches the SQLite driver, the AST firewall enforces:
1. **Single Statement Only**: Multi-statement query chaining (via `;`) is strictly prohibited.
2. **Read-Only Enforced**: Only queries starting with `SELECT` or `WITH ... SELECT` are permitted.
3. **Blacklisted Keywords**: Any presence of `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `ATTACH`, `DETACH`, `PRAGMA`, `VACUUM`, `REINDEX`, `LOAD_EXTENSION`, or `TRANSACTION` immediately triggers a `SECURITY_VIOLATION` verdict.
4. **Catalog Protection**: Queries attempting to query `sqlite_master`, `sqlite_schema`, or system catalog tables are blocked.
5. **Execution Timeout**: Ephemeral execution is limited to 2000ms to eliminate CPU exhaustion loops.

---

## 3. Result Verification Algorithm
Submissions are judged by comparing the result matrix with the pre-calculated expected result:
1. **Column Match**: Output column count must match the canonical schema.
2. **Row Order / Set Equality**: If the canonical solution includes an `ORDER BY`, row sequence is compared strictly. Otherwise, row multisets are verified for exact content equality.
3. **Null Handling**: Typed equality ensures `NULL` comparisons and numeric representations match standard SQL semantics.

---

## 4. Gamification & Progression Integration
- Solved SQL problems award **XP points** (15 XP for Easy, 30 XP for Medium, 50 XP for Hard).
- Successful query completions automatically contribute to the user's daily practice streak.
