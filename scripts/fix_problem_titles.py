"""Fix duplicate problem titles in SQLite and PostgreSQL databases."""

import asyncio
import sqlite3
import asyncpg

TITLES_MAP = {
    "bitwise-and-of-numbers-range": "Bitwise AND of Range Numbers",
    "kth-smallest-element-bst": "Kth Smallest Element in BST Inorder",
    "matrix-chain-multiplication-optimal": "Matrix Chain Multiplication Order Optimization",
    "minimum-path-sum-in-grid": "Minimum Path Sum in Grid DP",
    "search-rotated-sorted-array-target": "Search in Rotated Sorted Array for Target",
}

def fix_sqlite():
    conn = sqlite3.connect("dsaapp.db")
    cur = conn.cursor()
    for slug, new_title in TITLES_MAP.items():
        cur.execute("UPDATE problems SET title = ? WHERE slug = ?", (new_title, slug))
    conn.commit()
    conn.close()
    print("Fixed titles in dsaapp.db")

async def fix_postgres():
    pg = await asyncpg.connect("postgresql://dsaapp_user:DsaAppLocal2026Secure@localhost:5432/dsaapp")
    for slug, new_title in TITLES_MAP.items():
        await pg.execute("UPDATE problems SET title = $1 WHERE slug = $2", new_title, slug)
    await pg.close()
    print("Fixed titles in PostgreSQL")

if __name__ == "__main__":
    fix_sqlite()
    asyncio.run(fix_postgres())
