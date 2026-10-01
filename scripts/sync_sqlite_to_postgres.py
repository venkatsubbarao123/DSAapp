"""Sync data from SQLite (dsaapp.db) to PostgreSQL.

Reads the PostgreSQL connection URL securely from backend/.env.
"""

import asyncio
import datetime
import json
import os
import sqlite3
import uuid
from pathlib import Path

import asyncpg
from dotenv import load_dotenv


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

# This file is:
# DSAapp/scripts/sync_sqlite_to_postgres.py
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# SQLite database:
# DSAapp/dsaapp.db
SQLITE_DB = PROJECT_ROOT / "dsaapp.db"

# Environment file:
# DSAapp/backend/.env
ENV_FILE = BACKEND_DIR / ".env"


# ------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------

load_dotenv(ENV_FILE)

PG_URL = os.getenv("DATABASE_URL")

if not PG_URL:
    raise RuntimeError(
        f"DATABASE_URL is missing. "
        f"Please check: {ENV_FILE}"
    )

# Remove accidental surrounding quotes from .env
PG_URL = PG_URL.strip().strip('"').strip("'")


# ------------------------------------------------------------
# Tables
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Value conversion
# ------------------------------------------------------------

def sanitize_win1252(val):
    if not isinstance(val, str):
        return val

    replacements = {
        "\u03b1": "alpha",
        "\u2192": "->",
        "\u2190": "<-",
        "\u2194": "<->",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u2260": "!=",
        "\u221e": "infinity",
    }

    for old, new in replacements.items():
        val = val.replace(old, new)

    try:
        val.encode("cp1252")
        return val
    except UnicodeEncodeError:
        return val.encode(
            "cp1252",
            errors="ignore",
        ).decode("cp1252")


def parse_val(val, target_type, udt_name):
    if val is None:
        return None

    target = target_type.lower()
    udt = udt_name.lower()

    # Boolean
    if target == "boolean":
        if isinstance(val, (int, float)):
            return bool(val)

        if isinstance(val, str):
            return val.lower() in (
                "1",
                "true",
                "t",
                "yes",
            )

        return bool(val)

    # UUID
    if target == "uuid" or udt == "uuid":
        if isinstance(val, uuid.UUID):
            return val

        return uuid.UUID(str(val))

    # Timestamp / datetime
    if "timestamp" in target:
        if isinstance(
            val,
            (
                datetime.datetime,
                datetime.date,
            ),
        ):
            return val

        if isinstance(val, str):
            try:
                clean = val.strip().replace(
                    " ",
                    "T",
                )

                if clean.endswith("Z"):
                    clean = (
                        clean[:-1]
                        + "+00:00"
                    )

                return datetime.datetime.fromisoformat(
                    clean
                )

            except Exception:
                try:
                    return datetime.datetime.strptime(
                        val[:19],
                        "%Y-%m-%d %H:%M:%S",
                    )
                except Exception:
                    return datetime.datetime.now(
                        datetime.timezone.utc
                    )

    # JSON / JSONB
    if target in ("json", "jsonb"):
        if isinstance(val, (dict, list)):
            return json.dumps(
                val,
                ensure_ascii=False,
            )

        return str(val)

    # Integer
    if target in (
        "integer",
        "smallint",
        "bigint",
    ):
        return int(val)

    # Floating point / numeric
    if target in (
        "numeric",
        "real",
        "double precision",
    ):
        return float(val)

    # PostgreSQL enum / user-defined type
    if target == "user-defined":
        return str(val).strip()

    # Default string conversion
    return sanitize_win1252(str(val))


# ------------------------------------------------------------
# Main synchronization
# ------------------------------------------------------------

async def sync():
    print("=" * 60)
    print("DSAapp SQLite -> PostgreSQL Sync")
    print("=" * 60)

    print(f"SQLite database: {SQLITE_DB}")
    print(f"Environment file: {ENV_FILE}")

    if not SQLITE_DB.exists():
        raise FileNotFoundError(
            f"SQLite database not found: {SQLITE_DB}"
        )

    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f".env file not found: {ENV_FILE}"
        )

    # --------------------------------------------------------
    # SQLite connection
    # --------------------------------------------------------

    print("\nConnecting to SQLite...")

    sl = sqlite3.connect(
        str(SQLITE_DB)
    )

    sl.row_factory = sqlite3.Row

    print("SQLite connection successful.")

    # --------------------------------------------------------
    # PostgreSQL connection
    # --------------------------------------------------------

    print("\nConnecting to PostgreSQL from backend/.env...")

    pg = await asyncpg.connect(
        PG_URL
    )

    await pg.execute(
        "SET client_encoding TO 'UTF8';"
    )

    print("PostgreSQL connection successful.")

    # --------------------------------------------------------
    # Sync tables
    # --------------------------------------------------------

    total_inserted = 0
    total_errors = 0

    for table in TABLES_IN_ORDER:

        # Check SQLite table
        exists_sl = sl.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
            AND name = ?
            """,
            (table,),
        ).fetchone()[0]

        if not exists_sl:
            print(
                f"\n[{table}] "
                "SQLite table not found. Skipping."
            )
            continue

        # SQLite columns
        sl_info = sl.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()

        sl_cols = [
            row["name"]
            for row in sl_info
        ]

        # PostgreSQL columns
        pg_cols_info = await pg.fetch(
            """
            SELECT
                column_name,
                data_type,
                udt_name
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
            """,
            table,
        )

        if not pg_cols_info:
            print(
                f"\n[{table}] "
                "PostgreSQL table not found. Skipping."
            )
            continue

        pg_types = {
            row["column_name"]: row["data_type"]
            for row in pg_cols_info
        }

        pg_udts = {
            row["column_name"]: row["udt_name"]
            for row in pg_cols_info
        }

        # Only columns existing in both databases
        common_cols = [
            column
            for column in sl_cols
            if column in pg_types
        ]

        if not common_cols:
            print(
                f"\n[{table}] "
                "No common columns. Skipping."
            )
            continue

        # Read SQLite rows
        rows = sl.execute(
            f"""
            SELECT {", ".join(common_cols)}
            FROM {table}
            """
        ).fetchall()

        if not rows:
            print(
                f"\n[{table}] "
                "0 rows in SQLite."
            )
            continue

        print(
            f"\n--- Syncing {table}: "
            f"{len(rows)} rows ---"
        )

        # ----------------------------------------------------
        # Find primary key
        # ----------------------------------------------------

        pk_cols = [
            row["column_name"]
            for row in await pg.fetch(
                """
                SELECT c.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.constraint_column_usage ccu
                    USING (
                        constraint_schema,
                        constraint_name
                    )
                JOIN information_schema.columns c
                    ON c.table_schema =
                        tc.constraint_schema
                    AND c.table_name =
                        c.table_name
                    AND ccu.column_name =
                        c.column_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = $1
                """,
                table,
            )
        ]

        # ----------------------------------------------------
        # Build placeholders
        # ----------------------------------------------------

        placeholders = []

        for index, column in enumerate(
            common_cols
        ):
            parameter = f"${index + 1}"

            if pg_types[column] == "USER-DEFINED":
                placeholders.append(
                    f"{parameter}::{pg_udts[column]}"
                )
            else:
                placeholders.append(
                    parameter
                )

        column_names = ", ".join(
            common_cols
        )

        value_placeholders = ", ".join(
            placeholders
        )

        # ----------------------------------------------------
        # Build INSERT / UPSERT query
        # ----------------------------------------------------

        if pk_cols:

            primary_key = ", ".join(
                pk_cols
            )

            update_cols = [
                column
                for column in common_cols
                if column not in pk_cols
            ]

            if update_cols:

                update_items = []

                for column in update_cols:

                    if (
                        pg_types[column]
                        == "USER-DEFINED"
                    ):
                        update_items.append(
                            f"{column} = "
                            f"EXCLUDED.{column}::"
                            f"{pg_udts[column]}"
                        )
                    else:
                        update_items.append(
                            f"{column} = "
                            f"EXCLUDED.{column}"
                        )

                update_clause = ", ".join(
                    update_items
                )

                query = (
                    f"INSERT INTO {table} "
                    f"({column_names}) "
                    f"VALUES ({value_placeholders}) "
                    f"ON CONFLICT ({primary_key}) "
                    f"DO UPDATE SET "
                    f"{update_clause}"
                )

            else:

                query = (
                    f"INSERT INTO {table} "
                    f"({column_names}) "
                    f"VALUES ({value_placeholders}) "
                    f"ON CONFLICT ({primary_key}) "
                    f"DO NOTHING"
                )

        else:

            query = (
                f"INSERT INTO {table} "
                f"({column_names}) "
                f"VALUES ({value_placeholders}) "
                f"ON CONFLICT DO NOTHING"
            )

        # ----------------------------------------------------
        # Insert rows
        # ----------------------------------------------------

        inserted = 0
        errors = 0

        for row in rows:

            converted_row = []

            for column in common_cols:

                raw_value = row[column]

                target_type = pg_types[
                    column
                ]

                udt_name = pg_udts[
                    column
                ]

                try:
                    converted = parse_val(
                        raw_value,
                        target_type,
                        udt_name,
                    )

                except Exception:
                    converted = None

                converted_row.append(
                    converted
                )

            try:

                await pg.execute(
                    query,
                    *converted_row,
                )

                inserted += 1
                total_inserted += 1

            except Exception as error:

                errors += 1
                total_errors += 1

                if errors <= 3:
                    print(
                        f"ERROR in {table}: "
                        f"{error}"
                    )

        # ----------------------------------------------------
        # PostgreSQL count
        # ----------------------------------------------------

        pg_count = await pg.fetchval(
            f"SELECT COUNT(*) FROM {table}"
        )

        print(
            f"{table}: "
            f"{inserted} upserted, "
            f"{errors} errors, "
            f"PostgreSQL total = {pg_count}"
        )

    # --------------------------------------------------------
    # Close connections
    # --------------------------------------------------------

    await pg.close()
    sl.close()

    print("\n" + "=" * 60)
    print("SYNC FINISHED")
    print("=" * 60)
    print(
        f"Total rows upserted: {total_inserted}"
    )
    print(
        f"Total row errors: {total_errors}"
    )

    if total_errors == 0:
        print(
            "[SUCCESS] All tables synced successfully!"
        )
    else:
        print(
            "[WARNING] Sync completed with errors."
        )


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(sync())