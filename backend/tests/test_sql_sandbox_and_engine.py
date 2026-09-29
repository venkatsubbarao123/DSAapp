"""Unit and integration tests for SQL Sandbox, Security, and Practice Engine."""

import pytest
from httpx import AsyncClient

from backend.app.services.sql.sql_sandbox import SQLSandbox
from backend.app.services.sql.sql_service import SQLService


@pytest.mark.asyncio
async def test_sql_sandbox_valid_solution():
    """Verifies that an accurate query returns ACCEPTED in isolated sandbox."""
    schema_ddl = "CREATE TABLE users (id INT, name TEXT, age INT);"
    seed_sql = "INSERT INTO users VALUES (1, 'Alice', 25), (2, 'Bob', 30);"
    solution_sql = "SELECT name FROM users WHERE age > 26;"
    user_query = "SELECT name FROM users WHERE age > 26;"

    result = await SQLSandbox.evaluate_query(
        schema_ddl=schema_ddl,
        seed_data_sql=seed_sql,
        solution_sql=solution_sql,
        user_query=user_query,
    )

    assert result.verdict == "ACCEPTED"
    assert result.error_message is None
    assert result.user_columns == ["name"]
    assert result.user_rows == [["Bob"]]


@pytest.mark.asyncio
async def test_sql_sandbox_order_insensitive_matching():
    """Verifies that queries returning the same rows in different order pass order-insensitive checks."""
    schema_ddl = "CREATE TABLE items (id INT, val TEXT);"
    seed_sql = "INSERT INTO items VALUES (1, 'Alpha'), (2, 'Beta');"
    solution_sql = "SELECT val FROM items ORDER BY id ASC;"
    # User query returns in reverse order
    user_query = "SELECT val FROM items ORDER BY id DESC;"

    # 1. Order-insensitive: should be ACCEPTED
    res_unordered = await SQLSandbox.evaluate_query(
        schema_ddl=schema_ddl,
        seed_data_sql=seed_sql,
        solution_sql=solution_sql,
        user_query=user_query,
        is_order_sensitive=False,
    )
    assert res_unordered.verdict == "ACCEPTED"

    # 2. Order-sensitive: should be WRONG_ANSWER
    res_ordered = await SQLSandbox.evaluate_query(
        schema_ddl=schema_ddl,
        seed_data_sql=seed_sql,
        solution_sql=solution_sql,
        user_query=user_query,
        is_order_sensitive=True,
    )
    assert res_ordered.verdict == "WRONG_ANSWER"


@pytest.mark.asyncio
async def test_sql_sandbox_syntax_error():
    """Verifies that invalid SQL syntax produces SYNTAX_ERROR verdict safely."""
    schema_ddl = "CREATE TABLE test (id INT);"
    seed_sql = "INSERT INTO test VALUES (1);"
    solution_sql = "SELECT id FROM test;"
    user_query = "SELECT * FORM test;"  # typo: FORM

    res = await SQLSandbox.evaluate_query(
        schema_ddl=schema_ddl,
        seed_data_sql=seed_sql,
        solution_sql=solution_sql,
        user_query=user_query,
    )
    assert res.verdict == "SYNTAX_ERROR"
    assert "syntax error" in res.error_message.lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("forbidden_query", [
    "DROP TABLE users;",
    "DELETE FROM users WHERE id = 1;",
    "UPDATE users SET age = 99;",
    "INSERT INTO users VALUES (3, 'Eve', 40);",
    "ATTACH DATABASE ':memory:' AS evil;",
    "PRAGMA table_info(users);",
    "ALTER TABLE users ADD COLUMN hacked TEXT;",
    "SELECT * FROM sqlite_master;",
    "SELECT name FROM users; DROP TABLE users;",
])
async def test_sql_sandbox_security_firewall(forbidden_query: str):
    """CRITICAL SECURITY TEST: Blocks destructive statements, pragmas, and statement chaining."""
    is_safe, error_msg = SQLSandbox.validate_query_safety(forbidden_query)
    assert not is_safe
    assert error_msg is not None

    # Verify sandbox also refuses to execute it
    res = await SQLSandbox.evaluate_query(
        schema_ddl="CREATE TABLE users (id INT, name TEXT, age INT);",
        seed_data_sql="INSERT INTO users VALUES (1, 'Alice', 25);",
        solution_sql="SELECT name FROM users;",
        user_query=forbidden_query,
    )
    assert res.verdict == "FORBIDDEN_KEYWORD"


@pytest.mark.asyncio
async def test_sql_api_workflow(
    client: AsyncClient,
    db_session,
):
    """Tests the full API cycle for SQL problems: list, detail, dry-run, submit, history."""
    from backend.app.core.security import create_access_token
    from backend.app.models.user import User, UserRole

    # Create test user
    user = User(
        email="sql_student@example.com",
        hashed_password="hashed_pw",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token(user_id=user.id, role=user.role.value)
    auth_headers = {"Authorization": f"Bearer {token}"}

    # 1. List SQL problems
    list_res = await client.get("/api/v1/sql/problems", headers=auth_headers)
    assert list_res.status_code == 200
    problems = list_res.json()
    assert len(problems) >= 3
    target_problem = problems[0]
    slug = target_problem["slug"]

    # 2. Get problem detail
    detail_res = await client.get(f"/api/v1/sql/problems/{slug}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "schema_ddl" in detail
    assert "sample_data_sql" in detail

    # 3. Dry-run invalid query
    dry_fail = await client.post(
        f"/api/v1/sql/problems/{slug}/run",
        json={"query": "SELECT invalid_col FROM products;"},
        headers=auth_headers,
    )
    assert dry_fail.status_code == 200
    assert dry_fail.json()["verdict"] == "SYNTAX_ERROR"

    # 4. Dry-run valid query
    dry_ok = await client.post(
        f"/api/v1/sql/problems/{slug}/run",
        json={"query": "SELECT id, name FROM products;"},
        headers=auth_headers,
    )
    assert dry_ok.status_code == 200
    assert dry_ok.json()["verdict"] == "SUCCESS"
    assert len(dry_ok.json()["columns"]) == 2

    # 5. Submit correct query for "top-performing-products"
    correct_query = """
        SELECT p.name, SUM(p.price * oi.quantity) AS total_revenue
        FROM products p
        JOIN order_items oi ON p.id = oi.product_id
        GROUP BY p.id, p.name
        ORDER BY total_revenue DESC;
    """
    sub_res = await client.post(
        f"/api/v1/sql/problems/{slug}/submit",
        json={"query": correct_query},
        headers=auth_headers,
    )
    assert sub_res.status_code == 200
    sub_data = sub_res.json()
    assert sub_data["verdict"] == "ACCEPTED"
    assert sub_data["submission_id"] != ""

    # 6. List user submissions
    hist_res = await client.get(f"/api/v1/sql/problems/{slug}/submissions", headers=auth_headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1
    assert history[0]["verdict"] == "ACCEPTED"

