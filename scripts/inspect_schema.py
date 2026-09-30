import sqlite3

conn = sqlite3.connect('dsaapp.db')

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
print("Tables:", [t[0] for t in tables])

for table in tables:
    name = table[0]
    print(f"\n=== {name} ===")
    cols = conn.execute(f"PRAGMA table_info({name})").fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]}) pk={col[5]} notnull={col[3]} default={col[4]}")

conn.close()
