# DSAapp Complete Audit Report
# Generated: 2026-09-30

CRITICAL_ISSUES = [
    # --- CONTENT / DATABASE ---
    "DB-01: problems table has 0 rows — no content to display",
    "DB-02: topics table has 0 rows",
    "DB-03: lessons table has 0 rows",
    "DB-04: curricula table has 0 rows",
    "DB-05: patterns table has 0 rows",
    "DB-06: tags table has 0 rows",
    "DB-07: achievements table has 0 rows",
    "DB-08: daily_challenges table has 0 rows",
    "DB-09: sql_problems table has 0 rows",
    "DB-10: users table has 0 rows (clean slate)",

    # --- HOME PAGE ---
    "HOME-01: Hero says 'DSAapp Engineering Architecture' — developer text, not user-facing",
    "HOME-02: Hero badge says 'Phase 1 Foundation Operational' — developer label, violates PHASE U",
    "HOME-03: Primary CTA is 'Inspect Live Diagnostics' — wrong for beginner users",
    "HOME-04: Content cards describe security/database/judge architecture — developer docs not learning content",
    "HOME-05: No hero explanation of what DSAapp teaches",
    "HOME-06: No 'Start Learning' / 'Practice Problems' CTAs",
    "HOME-07: No topic preview grid",
    "HOME-08: No daily challenge section",
    "HOME-09: No 'Continue Learning' for authenticated users",
    "HOME-10: No guest experience design",

    # --- HEADER / NAVIGATION ---
    "NAV-01: Header has 18+ flat nav items — too crowded, no grouping",
    "NAV-02: Shows 'v0.7.0-phase7' version label — violates PHASE U",
    "NAV-03: Shows 'System Status' link in main nav — developer diagnostic, violates PHASE T",
    "NAV-04: Shows 'Overview' linking to developer diagnostics home",
    "NAV-05: No dropdown menus — all items at same level",
    "NAV-06: No mobile hamburger menu",
    "NAV-07: No theme toggle",
    "NAV-08: No global search",
    "NAV-09: Header overflows on tablet/mobile (no responsive handling)",
    "NAV-10: User badge shows raw 'role' (STUDENT/ADMIN) — not user-friendly",

    # --- PROBLEMS PAGE ---
    "PROB-01: Empty state says 'No matching problems found.' with no context (zero problems exist)",
    "PROB-02: Page title is 'Algorithmic Problem Directory' — stiff developer language",
    "PROB-03: No topic filter",
    "PROB-04: No pattern filter",
    "PROB-05: No status filter (solved/unsolved)",
    "PROB-06: No problem count shown when results exist",
    "PROB-07: 'Tier' column says 'FREE/PRO' — redundant alongside premium gate",

    # --- THEME SYSTEM ---
    "THEME-01: Only dark theme exists (tokens.css has only :root — no light theme, no system mode)",
    "THEME-02: No theme toggle in UI",
    "THEME-03: No theme persistence",

    # --- ACCESSIBILITY ---
    "A11Y-01: No ARIA roles on interactive cards",
    "A11Y-02: Missing aria-label on icon-only buttons",
    "A11Y-03: No focus management on modal open",

    # --- UX / DEVELOPER DIAGNOSTICS IN UI ---
    "UX-01: SystemStatusPage exposes raw backend diagnostics to all users",
    "UX-02: Home page describes internal architecture (security layers, DB, judge) to users",
    "UX-03: Version label in header (v0.7.0-phase7)",
    "UX-04: Phase labels throughout UI (Phase 1 Foundation Operational)",

    # --- SEEDING ---
    "SEED-01: No seed script exists for problems",
    "SEED-02: No seed script exists for topics/lessons/curriculum",
    "SEED-03: No seed script exists for achievements",
    "SEED-04: No seed script exists for sql_problems",
    "SEED-05: No seed script exists for patterns/tags",
]

print(f"Total critical issues found: {len(CRITICAL_ISSUES)}")
for i in CRITICAL_ISSUES:
    print(f"  {i}")
