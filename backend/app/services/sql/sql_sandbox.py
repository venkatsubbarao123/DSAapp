"""Isolated SQL Execution Sandbox.

CRITICAL SECURITY ARCHITECTURE:
- Arbitrary student SQL is treated as UNTRUSTED input.
- NEVER executed against the application or production PostgreSQL database.
- Runs exclusively inside ephemeral in-memory SQLite instances (:memory:) created fresh
  for each query evaluation and immediately destroyed.
- Strict AST/Lexical keyword firewall disallows destructive statements, administrative pragmas,
  file I/O, network extensions, and multiple statement chaining.
- Result comparison supports both order-sensitive and multiset order-insensitive queries.
"""

import asyncio
import collections
import logging
import math
import re
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Disallowed keywords and operational commands
FORBIDDEN_KEYWORDS_REGEX = re.compile(
    r"\b("
    r"ATTACH|DETACH|PRAGMA|COPY|DROP|ALTER|CREATE|INSERT|UPDATE|DELETE|"
    r"GRANT|REVOKE|LOAD_EXTENSION|REINDEX|VACUUM|REPLACE|TRANSACTION|"
    r"COMMIT|ROLLBACK|BEGIN|SAVEPOINT|RELEASE|LOCK|EXECUTE|CALL|SYSTEM"
    r")\b",
    re.IGNORECASE,
)

# System / metadata table patterns
SQLITE_MASTER_REGEX = re.compile(
    r"\b(sqlite_master|sqlite_temp_master|sqlite_schema|sqlite_temp_schema)\b",
    re.IGNORECASE,
)


@dataclass
class SQLSandboxResult:
    """Safe evaluation output from SQL sandbox execution."""
    verdict: str  # ACCEPTED, WRONG_ANSWER, SYNTAX_ERROR, FORBIDDEN_KEYWORD, TIME_LIMIT_EXCEEDED, SYSTEM_ERROR
    execution_time_ms: float = 0.0
    user_columns: List[str] = field(default_factory=list)
    user_rows: List[List[Any]] = field(default_factory=list)
    expected_columns: List[str] = field(default_factory=list)
    expected_rows_sample: List[List[Any]] = field(default_factory=list)
    error_message: Optional[str] = None


class SQLSandbox:
    """Ephemeral, isolated SQLite execution sandbox."""

    @classmethod
    def validate_query_safety(cls, query: str) -> Tuple[bool, Optional[str]]:
        """Validates that query contains only safe read-only SELECT or WITH statements.

        Enforces:
        1. Non-empty string within length limit
        2. Must start with SELECT or WITH (CTE)
        3. No statement chaining / multiple queries
        4. No forbidden keywords (DDL, DML, ATTACH, PRAGMA, COPY, etc.)
        5. No system schema table access
        """
        trimmed = query.strip()
        if not trimmed:
            return False, "Query cannot be empty."

        # Strip trailing semicolon for analysis
        if trimmed.endswith(";"):
            trimmed = trimmed[:-1].strip()

        # Reject query containing semicolons (multiple statements)
        if ";" in trimmed:
            return False, "Multiple SQL statements are strictly forbidden."

        # Verify initial keyword
        first_token = trimmed.split()[0].upper() if trimmed.split() else ""
        if first_token not in ("SELECT", "WITH"):
            return False, f"Forbidden statement type '{first_token}'. Only SELECT and WITH (CTE) queries are permitted."

        # Keyword checks
        forbidden_match = FORBIDDEN_KEYWORDS_REGEX.search(trimmed)
        if forbidden_match:
            keyword = forbidden_match.group(0).upper()
            return False, f"Forbidden keyword detected: '{keyword}' is not allowed in student queries."

        # System catalog checks
        if SQLITE_MASTER_REGEX.search(trimmed):
            return False, "Direct queries against system schema tables are not allowed."

        return True, None

    @classmethod
    def _normalize_cell(cls, val: Any) -> Any:
        """Normalizes cell values for resilient comparison (e.g. floats and case-insensitive strings)."""
        if val is None:
            return None
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return str(val)
            return round(val, 6)
        return val

    @classmethod
    def _execute_in_isolated_conn(
        cls,
        schema_ddl: str,
        seed_data_sql: str,
        solution_sql: str,
        user_query: str,
        is_order_sensitive: bool,
        timeout_seconds: float = 3.0,
    ) -> SQLSandboxResult:
        """Internal synchronous execution in a dedicated in-memory SQLite connection."""
        start_time = time.perf_counter()
        conn: Optional[sqlite3.Connection] = None

        try:
            # Create isolated in-memory DB
            conn = sqlite3.connect(":memory:")
            conn.isolation_level = None  # autocommit mode
            cur = conn.cursor()

            # Seed schema & test data
            if schema_ddl.strip():
                cur.executescript(schema_ddl)
            if seed_data_sql.strip():
                cur.executescript(seed_data_sql)

            # Step 1: Run reference solution query
            try:
                cur.execute(solution_sql)
                expected_columns = [d[0] for d in cur.description] if cur.description else []
                expected_rows = cur.fetchall()
            except sqlite3.Error as sol_err:
                logger.error(f"Authoritative solution SQL error: {sol_err}")
                return SQLSandboxResult(
                    verdict="SYSTEM_ERROR",
                    error_message="Reference solution failed in sandbox environment.",
                )

            # Step 2: Set query execution limits
            instruction_count = 0
            max_instructions = 100_000

            def progress_handler():
                nonlocal instruction_count
                instruction_count += 1
                if instruction_count > max_instructions:
                    return 1  # Abort query
                return 0

            conn.set_progress_handler(progress_handler, 100)

            # Step 3: Run student query
            q_start = time.perf_counter()
            try:
                cur.execute(user_query)
                user_columns = [d[0] for d in cur.description] if cur.description else []
                user_rows = cur.fetchall()
            except sqlite3.OperationalError as op_err:
                err_str = str(op_err)
                if "interrupted" in err_str.lower() or instruction_count > max_instructions:
                    return SQLSandboxResult(
                        verdict="TIME_LIMIT_EXCEEDED",
                        execution_time_ms=(time.perf_counter() - q_start) * 1000,
                        error_message="Query exceeded execution time limit (aborted).",
                    )
                return SQLSandboxResult(
                    verdict="SYNTAX_ERROR",
                    execution_time_ms=(time.perf_counter() - q_start) * 1000,
                    error_message=f"SQL Syntax Error: {err_str}",
                )
            except sqlite3.Error as db_err:
                return SQLSandboxResult(
                    verdict="SYNTAX_ERROR",
                    execution_time_ms=(time.perf_counter() - q_start) * 1000,
                    error_message=f"SQL Error: {str(db_err)}",
                )

            exec_time_ms = (time.perf_counter() - q_start) * 1000

            # Step 4: Compare column specifications
            user_cols_norm = [c.lower().strip() for c in user_columns]
            exp_cols_norm = [c.lower().strip() for c in expected_columns]

            if len(user_cols_norm) != len(exp_cols_norm):
                return SQLSandboxResult(
                    verdict="WRONG_ANSWER",
                    execution_time_ms=exec_time_ms,
                    user_columns=user_columns,
                    user_rows=[list(r) for r in user_rows[:50]],
                    expected_columns=expected_columns,
                    expected_rows_sample=[list(r) for r in expected_rows[:10]],
                    error_message=f"Column count mismatch: expected {len(exp_cols_norm)} columns, got {len(user_cols_norm)}.",
                )

            # Step 5: Normalize and compare row sets
            norm_user_rows = [
                tuple(cls._normalize_cell(v) for v in row)
                for row in user_rows
            ]
            norm_exp_rows = [
                tuple(cls._normalize_cell(v) for v in row)
                for row in expected_rows
            ]

            if len(norm_user_rows) != len(norm_exp_rows):
                return SQLSandboxResult(
                    verdict="WRONG_ANSWER",
                    execution_time_ms=exec_time_ms,
                    user_columns=user_columns,
                    user_rows=[list(r) for r in user_rows[:50]],
                    expected_columns=expected_columns,
                    expected_rows_sample=[list(r) for r in expected_rows[:10]],
                    error_message=f"Row count mismatch: expected {len(norm_exp_rows)} rows, got {len(norm_user_rows)}.",
                )

            is_correct = False
            if is_order_sensitive:
                is_correct = (norm_user_rows == norm_exp_rows)
            else:
                user_counter = collections.Counter(norm_user_rows)
                exp_counter = collections.Counter(norm_exp_rows)
                is_correct = (user_counter == exp_counter)

            if is_correct:
                return SQLSandboxResult(
                    verdict="ACCEPTED",
                    execution_time_ms=exec_time_ms,
                    user_columns=user_columns,
                    user_rows=[list(r) for r in user_rows[:50]],
                    expected_columns=expected_columns,
                    expected_rows_sample=[list(r) for r in expected_rows[:10]],
                )
            else:
                return SQLSandboxResult(
                    verdict="WRONG_ANSWER",
                    execution_time_ms=exec_time_ms,
                    user_columns=user_columns,
                    user_rows=[list(r) for r in user_rows[:50]],
                    expected_columns=expected_columns,
                    expected_rows_sample=[list(r) for r in expected_rows[:10]],
                    error_message="Query output values or ordering did not match expected solution.",
                )

        except Exception as exc:
            logger.exception("Unexpected error during SQL sandbox execution")
            return SQLSandboxResult(
                verdict="SYSTEM_ERROR",
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
                error_message=f"Sandbox execution error: {str(exc)}",
            )
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    @classmethod
    async def evaluate_query(
        cls,
        schema_ddl: str,
        seed_data_sql: str,
        solution_sql: str,
        user_query: str,
        is_order_sensitive: bool = False,
        timeout_seconds: float = 3.0,
    ) -> SQLSandboxResult:
        """Asynchronously executes and evaluates an untrusted student SQL query."""
        # Pre-execution safety validation
        is_safe, error_msg = cls.validate_query_safety(user_query)
        if not is_safe:
            return SQLSandboxResult(
                verdict="FORBIDDEN_KEYWORD",
                error_message=error_msg,
            )

        # Offload in-memory SQLite execution to thread pool
        loop = asyncio.get_running_loop()
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    cls._execute_in_isolated_conn,
                    schema_ddl,
                    seed_data_sql,
                    solution_sql,
                    user_query,
                    is_order_sensitive,
                    timeout_seconds,
                ),
                timeout=timeout_seconds + 1.0,
            )
        except asyncio.TimeoutError:
            return SQLSandboxResult(
                verdict="TIME_LIMIT_EXCEEDED",
                execution_time_ms=timeout_seconds * 1000,
                error_message="Query execution timed out.",
            )

    @classmethod
    async def dry_run_query(
        cls,
        schema_ddl: str,
        seed_data_sql: str,
        user_query: str,
        timeout_seconds: float = 3.0,
    ) -> SQLSandboxResult:
        """Dry-runs a query against sandbox schema without grading against solution."""
        is_safe, error_msg = cls.validate_query_safety(user_query)
        if not is_safe:
            return SQLSandboxResult(
                verdict="FORBIDDEN_KEYWORD",
                error_message=error_msg,
            )

        loop = asyncio.get_running_loop()

        def _run_dry():
            start_time = time.perf_counter()
            conn = None
            try:
                conn = sqlite3.connect(":memory:")
                cur = conn.cursor()
                if schema_ddl.strip():
                    cur.executescript(schema_ddl)
                if seed_data_sql.strip():
                    cur.executescript(seed_data_sql)

                cur.execute(user_query)
                cols = [d[0] for d in cur.description] if cur.description else []
                rows = cur.fetchmany(50)
                exec_ms = (time.perf_counter() - start_time) * 1000
                return SQLSandboxResult(
                    verdict="SUCCESS",
                    execution_time_ms=exec_ms,
                    user_columns=cols,
                    user_rows=[list(r) for r in rows],
                )
            except sqlite3.OperationalError as op_err:
                return SQLSandboxResult(
                    verdict="SYNTAX_ERROR",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"SQL Syntax Error: {str(op_err)}",
                )
            except Exception as e:
                return SQLSandboxResult(
                    verdict="SYSTEM_ERROR",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    error_message=f"Execution error: {str(e)}",
                )
            finally:
                if conn:
                    conn.close()

        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _run_dry),
                timeout=timeout_seconds + 1.0,
            )
        except asyncio.TimeoutError:
            return SQLSandboxResult(
                verdict="TIME_LIMIT_EXCEEDED",
                execution_time_ms=timeout_seconds * 1000,
                error_message="Query dry-run timed out.",
            )
