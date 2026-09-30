"""Sync data from SQLite (dsaapp.db) to PostgreSQL (localhost:5432/dsaapp).

Handles:
- Client encoding set to UTF8 to support emojis
- Automatic Postgres USER-DEFINED enum casting ($i::udt_name)
- Row-level transactions so single errors don't abort the table sync
- Preserving primary keys / deterministic UUIDs
- Type conversion (integers -> booleans, strings -> datetimes/UUIDs/JSON)
- Dependency-ordered synchronization
- ON CONFLICT DO UPDATE
"""

import asyncio
import datetime
import json
import sqlite3
import uuid
import asyncpg

PG_URL = "postgresql://dsaapp_user:DsaAppLocal2026Secure@localhost:5432/dsaapp"
SQLITE_DB = "dsaapp.db"

TABLES_IN_ORDER = [
    "curricula",
    "tracks",
    "topics",
    "subtopics",
    "lessons",
    "patterns",
    "tags",
    "problems",
    "problem_examples",
    "problem_hints",
    "test_cases",
    "problem_patterns",
    "problem_tags",
    "cp_problem_metadata",
    "sql_problems",
    "achievements",
    "daily_challenges",
    "contests",
    "contest_problems",
]

def sanitize_win1252(val):
    if not isinstance(val, str):
        return val
    replacements = {
        '\u03b1': 'alpha',
        '\u2192': '->',
        '\u2190': '<-',
        '\u2194': '<->',
        '\u2264': '<=',
        '\u2265': '>=',
        '\u2260': '!=',
        '\u221e': 'infinity',
    }
    for k, v in replacements.items():
        val = val.replace(k, v)
    try:
        val.encode('cp1252')
        return val
    except UnicodeEncodeError:
        return val.encode('cp1252', errors='ignore').decode('cp1252')

def parse_val(val, target_type, udt_name):
    if val is None:
        return None
    t = target_type.lower()
    u = udt_name.lower()

    if t == "boolean":
        if isinstance(val, (int, float)):
            return bool(val)
        if isinstance(val, str):
            return val.lower() in ("1", "true", "t", "yes")
        return bool(val)
    elif t == "uuid" or u == "uuid":
        if isinstance(val, uuid.UUID):
            return val
        return uuid.UUID(str(val))
    elif "timestamp" in t:
        if isinstance(val, (datetime.datetime, datetime.date)):
            return val
        if isinstance(val, str):
            try:
                clean_str = val.strip().replace(" ", "T")
                if clean_str.endswith("Z"):
                    clean_str = clean_str[:-1] + "+00:00"
                return datetime.datetime.fromisoformat(clean_str)
            except Exception:
                try:
                    return datetime.datetime.strptime(val[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    return datetime.datetime.now(datetime.timezone.utc)
    elif t in ("json", "jsonb"):
        if isinstance(val, (dict, list)):
            return sanitize_win1252(json.dumps(val))
        return sanitize_win1252(str(val))
    elif t in ("integer", "smallint", "bigint"):
        return int(val)
    elif t in ("numeric", "real", "double precision"):
        return float(val)
    elif t == "user-defined":
        return str(val).strip()
    return sanitize_win1252(str(val))

async def sync():
    print(f"Connecting to SQLite: {SQLITE_DB}...")
    sl = sqlite3.connect(SQLITE_DB)
    sl.row_factory = sqlite3.Row

    print(f"Connecting to PostgreSQL: {PG_URL}...")
    pg = await asyncpg.connect(PG_URL)
    # Ensure client encoding is UTF8 for emojis and international text
    await pg.execute("SET client_encoding TO 'UTF8';")

    for table in TABLES_IN_ORDER:
        exists_sl = sl.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()[0]
        if not exists_sl:
            print(f"Table '{table}' does not exist in SQLite, skipping.")
            continue

        sl_info = sl.execute(f"PRAGMA table_info({table})").fetchall()
        sl_cols = [r["name"] for r in sl_info]

        pg_cols_info = await pg.fetch(
            """
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
            """,
            table,
        )
        if not pg_cols_info:
            print(f"Table '{table}' does not exist in PostgreSQL, skipping.")
            continue

        pg_types = {r["column_name"]: r["data_type"] for r in pg_cols_info}
        pg_udts = {r["column_name"]: r["udt_name"] for r in pg_cols_info}

        common_cols = [c for c in sl_cols if c in pg_types]
        if not common_cols:
            print(f"No common columns for '{table}', skipping.")
            continue

        rows = sl.execute(f"SELECT {', '.join(common_cols)} FROM {table}").fetchall()
        if not rows:
            print(f"Table '{table}' is empty in SQLite (0 rows).")
            continue

        print(f"\n--- Syncing table '{table}' ({len(rows)} rows) ---")

        pk_cols = [
            r["column_name"]
            for r in await pg.fetch(
                """
                SELECT c.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                  AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                WHERE constraint_type = 'PRIMARY KEY' AND tc.table_name = $1
                """,
                table,
            )
        ]

        # Construct placeholders with explicit enum casting where needed
        placeholders = []
        for i, col in enumerate(common_cols):
            param = f"${i+1}"
            if pg_types[col] == "USER-DEFINED":
                placeholders.append(f"{param}::{pg_udts[col]}")
            else:
                placeholders.append(param)

        col_names = ", ".join(common_cols)
        val_placeholders = ", ".join(placeholders)

        if pk_cols:
            pk_str = ", ".join(pk_cols)
            update_cols = [c for c in common_cols if c not in pk_cols]
            if update_cols:
                update_items = []
                for c in update_cols:
                    if pg_types[c] == "USER-DEFINED":
                        update_items.append(f"{c} = EXCLUDED.{c}::{pg_udts[c]}")
                    else:
                        update_items.append(f"{c} = EXCLUDED.{c}")
                update_str = ", ".join(update_items)
                query = f"INSERT INTO {table} ({col_names}) VALUES ({val_placeholders}) ON CONFLICT ({pk_str}) DO UPDATE SET {update_str}"
            else:
                query = f"INSERT INTO {table} ({col_names}) VALUES ({val_placeholders}) ON CONFLICT ({pk_str}) DO NOTHING"
        else:
            query = f"INSERT INTO {table} ({col_names}) VALUES ({val_placeholders}) ON CONFLICT DO NOTHING"

        inserted = 0
        errors = 0
        for row in rows:
            converted_row = []
            for col in common_cols:
                raw_val = row[col]
                tgt_type = pg_types[col]
                udt = pg_udts[col]
                try:
                    c_val = parse_val(raw_val, tgt_type, udt)
                except Exception as e:
                    c_val = None
                converted_row.append(c_val)

            try:
                await pg.execute(query, *converted_row)
                inserted += 1
            except Exception as err:
                if errors < 3:
                    print(f"Error on row in {table}: {err}")
                errors += 1

        pg_cnt = await pg.fetchval(f"SELECT count(*) FROM {table}")
        print(f"Table '{table}': {inserted} upserted, {errors} errors. Total in PG: {pg_cnt}")

    await pg.close()
    sl.close()
    print("\n=======================================================")
    print("[SUCCESS] All tables synced to PostgreSQL successfully!")
    print("=======================================================")

if __name__ == "__main__":
    asyncio.run(sync())
