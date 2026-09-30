import sqlite3
conn = sqlite3.connect('dsaapp.db')
cur = conn.cursor()

# problems schema
cur.execute("PRAGMA table_info(problems)")
print("PROBLEMS COLUMNS:", [c[1] for c in cur.fetchall()])
cur.execute("SELECT count(*) FROM problems")
print("TOTAL PROBLEMS:", cur.fetchone()[0])

# Check status column values
cur.execute("SELECT DISTINCT status FROM problems")
print("PROBLEM STATUSES:", cur.fetchall())

# Other tables
for tbl in ['topics', 'lessons', 'curricula', 'patterns', 'tags', 'achievements', 'daily_challenges', 'sql_problems', 'users']:
    cur.execute(f"SELECT count(*) FROM {tbl}")
    print(f"{tbl}: {cur.fetchone()[0]}")

# Curricula schema
cur.execute("PRAGMA table_info(curricula)")
print("\nCURRICULA COLS:", [c[1] for c in cur.fetchall()])

# Topics schema
cur.execute("PRAGMA table_info(topics)")
print("TOPICS COLS:", [c[1] for c in cur.fetchall()])

# Lessons schema
cur.execute("PRAGMA table_info(lessons)")
print("LESSONS COLS:", [c[1] for c in cur.fetchall()])

conn.close()
