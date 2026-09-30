import sqlite3

conn = sqlite3.connect('dsaapp.db')

tables_of_interest = ['achievements', 'daily_challenges', 'sql_problems', 'patterns', 'problem_hints', 'problem_patterns', 'problem_tags', 'curricula', 'tracks', 'topics', 'subtopics', 'lessons']

for name in tables_of_interest:
    print(f"\n=== {name} ===")
    cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]}) pk={col[5]} notnull={col[3]} default={col[4]}")

conn.close()
