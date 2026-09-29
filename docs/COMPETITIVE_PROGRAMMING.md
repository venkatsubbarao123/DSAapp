# DSAapp Competitive Programming System

## Overview
Phase 8 integrates a full **Competitive Programming (CP) Framework** modeled on modern competitive platforms (Codeforces, AtCoder, ICPC), connecting the curriculum with curated rated problems and an independent Elo-style rating engine.

---

## 1. Rating Bands & Ladders
Problems and participants are organized into standardized competitive divisions:

| Band | Rating Range | Title | Color Token | Description |
|---|---|---|---|---|
| **DIV_4** | 800 – 1199 | Newbie / Pupil | `#94a3b8` | Basic syntax, direct simulation, simple math, elementary arrays |
| **DIV_3** | 1200 – 1599 | Specialist / Expert | `#3b82f6` | Two pointers, binary search, greedy algorithms, basic graphs |
| **DIV_2** | 1600 – 1999 | Candidate Master | `#f59e0b` | Dynamic programming, shortest paths, segment trees, combinatorics |
| **DIV_1** | 2000 – 2400+ | Master / Grandmaster | `#ef4444` | Flow networks, heavy-light decomposition, advanced math, FFT |

---

## 2. Competitive Rating Tracking vs Practice Rating
- **Competitive Rating (`current_rating`, `max_rating`)**:
  - Dynamically updated based on performance in official arena contests.
  - Distinct from the Phase 7 gamification practice score.
  - Calculated using expected score calculations and actual ranking in each contest.
  - Stored with full audit history in `competitive_rating_history`.
- **Rank Titles**:
  - Automatically granted and updated on the user profile as rating thresholds are crossed.

---

## 3. Problem Catalog & Metadata
Each CP problem record tracks:
- Canonical difficulty rating (e.g., 800, 1400, 2100).
- Topic tags (e.g., `dp`, `graphs`, `greedy`, `math`, `data structures`).
- Platform linkage (e.g., Codeforces contest ID + problem index like `4A`, `71A`).
- Aggregated solve metrics and user solve state.
