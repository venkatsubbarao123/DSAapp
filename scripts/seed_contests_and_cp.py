"""Idempotent seed script for Contests and Competitive Programming metadata."""

import sqlite3
import shutil
import uuid
from datetime import datetime, timedelta, timezone

DB_PATH = "dsaapp.db"
BACKEND_DB_PATH = "backend/dsaapp.db"

def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. Fetch available problems
    cur.execute("SELECT id, slug, title, difficulty FROM problems ORDER BY display_order ASC")
    problems = cur.fetchall()
    print(f"Found {len(problems)} problems to map CP metadata to.")

    # 2. Seed CP Problem Metadata
    # Assign rating bands based on difficulty
    seeded_cp = 0
    for prob_id, slug, title, difficulty in problems:
        cur.execute("SELECT id FROM cp_problem_metadata WHERE problem_id = ?", (prob_id,))
        if cur.fetchone():
            continue

        if difficulty == "EASY":
            band = 800 + (hash(slug) % 4) * 100  # 800, 900, 1000, 1100
        elif difficulty == "MEDIUM":
            band = 1200 + (hash(slug) % 4) * 100  # 1200, 1300, 1400, 1500
        elif difficulty == "HARD":
            band = 1600 + (hash(slug) % 4) * 100  # 1600, 1700, 1800, 1900
        else:
            band = 2000 + (hash(slug) % 3) * 200  # 2000, 2200, 2400

        meta_id = str(uuid.uuid4())
        input_fmt = "The first line contains test case parameters. The subsequent lines contain the array elements."
        output_fmt = "Output the computed result on a single line."
        constraints = "1 <= N <= 200,000\n-10^9 <= A[i] <= 10^9\nTime limit: 1.0s"
        editorial = f"Optimal algorithmic solution for {title} utilizing appropriate invariant management."

        cur.execute("""
            INSERT INTO cp_problem_metadata (id, problem_id, rating_band, time_limit_ms, memory_limit_mb, input_format, output_format, constraints, editorial)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (meta_id, prob_id, band, 1000, 256, input_fmt, output_fmt, constraints, editorial))
        seeded_cp += 1

    print(f"Seeded {seeded_cp} CP problem metadata records.")

    # 3. Seed Contests
    now = datetime.now(timezone.utc)
    contests_data = [
        {
            "slug": "dsa-weekly-round-1",
            "title": "DSA Weekly Championship Round 1",
            "description": "Weekly rating-rated algorithmic sprint. 4 problems, 90 minutes. ICPC penalties apply.",
            "status": "LIVE",
            "start_at": (now - timedelta(minutes=30)).isoformat(),
            "end_at": (now + timedelta(minutes=60)).isoformat(),
            "duration_seconds": 5400,
            "visibility": "PUBLIC",
            "premium_required": 0,
        },
        {
            "slug": "global-algorithmic-sprint-2026",
            "title": "Global Algorithmic Sprint 2026",
            "description": "Premier international coding round with dynamic scoring and live scoreboards.",
            "status": "UPCOMING",
            "start_at": (now + timedelta(days=3)).isoformat(),
            "end_at": (now + timedelta(days=3, hours=2)).isoformat(),
            "duration_seconds": 7200,
            "visibility": "PUBLIC",
            "premium_required": 0,
        },
        {
            "slug": "inaugural-speed-dsa-clash",
            "title": "Inaugural Speed DSA Clash",
            "description": "Fast-paced division sprint focusing on string algorithms, prefix trees, and dynamic programming.",
            "status": "ENDED",
            "start_at": (now - timedelta(days=7)).isoformat(),
            "end_at": (now - timedelta(days=7, hours=-2)).isoformat(),
            "duration_seconds": 7200,
            "visibility": "PUBLIC",
            "premium_required": 0,
        },
    ]

    seeded_contests = 0
    seeded_contest_problems = 0
    for c in contests_data:
        cur.execute("SELECT id FROM contests WHERE slug = ?", (c["slug"],))
        existing = cur.fetchone()
        if existing:
            continue

        c_id = str(uuid.uuid4())
        created_at = (now - timedelta(days=1)).isoformat()
        cur.execute("""
            INSERT INTO contests (id, title, slug, description, status, start_at, end_at, duration_seconds, visibility, premium_required, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (c_id, c["title"], c["slug"], c["description"], c["status"], c["start_at"], c["end_at"], c["duration_seconds"], c["visibility"], c["premium_required"], created_at, created_at))
        seeded_contests += 1

        # Associate 4 problems with each contest
        sample_probs = problems[:4]
        for seq, (prob_id, _, _, diff) in enumerate(sample_probs, start=1):
            cp_id = str(uuid.uuid4())
            points = seq * 250
            cur.execute("""
                INSERT INTO contest_problems (id, contest_id, problem_id, sequence, points, penalty_minutes, difficulty)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cp_id, c_id, prob_id, seq, points, 20, diff))
            seeded_contest_problems += 1

    print(f"Seeded {seeded_contests} contests with {seeded_contest_problems} contest problems.")

    conn.commit()
    conn.close()

    # Synchronize to backend/dsaapp.db
    shutil.copy2(DB_PATH, BACKEND_DB_PATH)
    print("Database synchronized to backend/dsaapp.db successfully.")

if __name__ == "__main__":
    seed()
