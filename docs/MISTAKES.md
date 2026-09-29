# Mistake Notebook Architecture

## Overview
The Mistake Notebook allows students to systematically record, categorize, diagnose, and resolve errors encountered during algorithmic problem-solving. Research demonstrates that active mistake reflection significantly accelerates pattern recognition and interview readiness.

---

## 1. Mistake Taxonomy (`MistakeType`)

Each mistake entry is classified under a structured taxonomy:

| Category | Identifier | Description |
|---|---|---|
| **Concept Gap** | `CONCEPT_GAP` | Unfamiliarity with underlying mathematical/algorithmic principle |
| **Logic Error** | `LOGIC_ERROR` | Flawed reasoning, incorrect invariant, or inverted condition |
| **Edge Case** | `EDGE_CASE` | Unhandled boundary conditions (e.g. empty array, single node, duplicates) |
| **Complexity Issue** | `COMPLEXITY_ISSUE` | Algorithm exceeds required time or space constraints ($O(n^2)$ vs $O(n)$) |
| **Syntax Error** | `SYNTAX_ERROR` | Language grammar mistakes or incorrect standard library usage |
| **Implementation Error**| `IMPLEMENTATION_ERROR` | Off-by-one indices, incorrect pointer updates, uninitialized variables |
| **Misunderstanding** | `MISUNDERSTANDING` | Misinterpreting problem statement or constraints |
| **Other** | `OTHER` | Miscellaneous cognitive or environment hurdles |

---

## 2. Privacy & IDOR Immunity
- Mistakes are strictly private to the authenticated creator.
- Query filters enforce `user_id == current_user.id`.
- Modifying (`PATCH /api/v1/mistakes/{id}`) or deleting (`DELETE /api/v1/mistakes/{id}`) any mistake record belonging to another student returns HTTP 404 (not 403), avoiding user existence enumeration.

---

## 3. Data Model: `Mistake`

- `id`: Internal UUID primary key
- `public_id`: Alphanumeric public ID (`mst_...`)
- `user_id`: Owning user FK (indexed)
- `problem_id`: Optional FK to `problems.id` (nullable, set NULL on delete)
- `lesson_id`: Optional FK to `lessons.id` (nullable, set NULL on delete)
- `mistake_type`: Structured enum
- `title`: Short title (max 255 chars)
- `description`: Detailed reflection on what went wrong
- `correction`: Solution takeaway / rule of thumb (nullable)
- `is_resolved`: Boolean flag (default `False`)
- `resolved_at`: UTC timestamp when marked resolved

---

## 4. Search and Filtering
The mistake notebook API supports:
- `mistake_type`: Filter by category
- `is_resolved`: Filter by resolution state (`true` / `false`)
- `search`: Keyword search matching `title` or `description` (case-insensitive)
- `skip` and `limit`: Standard pagination
