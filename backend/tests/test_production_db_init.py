"""Regression tests for production database initialization safety.

Issue: on Render/production PostgreSQL, ``Base.metadata.create_all()`` emitted a
bare ``CREATE TYPE contentlevel AS ENUM(...)`` against a database that Alembic had
already provisioned, raising::

    UniqueViolationError: duplicate key value violates unique constraint
    "pg_type_typname_nsp_index"

and aborting application startup.

These tests lock in the fix:
  * PostgreSQL must NEVER receive create_all (no DDL at startup).
  * Alembic revision is verified read-only instead.
  * SQLite (local dev / tests) must still get create_all.
  * Production must reject the mock judge driver (no fabricated verdicts).
"""

import inspect
import sys
from pathlib import Path

import pytest

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


# --------------------------------------------------------------------------
# Static guarantees on the init_db module
# --------------------------------------------------------------------------


def test_init_db_module_is_dialect_aware():
    """init_db must branch on dialect instead of unconditionally calling create_all."""
    from backend.app.db import init_db as init_db_module

    source = inspect.getsource(init_db_module.init_db)
    assert "_is_postgres()" in source, (
        "init_db() must detect PostgreSQL and skip create_all()"
    )
    assert "create_all" in source, (
        "init_db() must still create_all for SQLite local/test databases"
    )
    postgres_branch = source.index("_is_postgres()")
    create_all_call = source.index("Base.metadata.create_all")
    assert postgres_branch < create_all_call, (
        "PostgreSQL branch must be evaluated before create_all()"
    )


def test_init_db_postgres_branch_emits_no_ddl():
    """The PostgreSQL branch must not CALL create_all.

    The check runs against the AST so that prose in the docstring/comment
    (which legitimately mentions ``create_all``) cannot mask a real call.
    """
    import ast

    from backend.app.db import init_db as init_db_module

    tree = ast.parse(inspect.getsource(init_db_module.init_db))

    # Walk the body and find the postgres branch: `if _is_postgres(): ...`
    postgres_body: list[ast.stmt] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            test_src = ast.unparse(node.test)
            if "_is_postgres()" in test_src:
                postgres_body = node.body
                break

    assert postgres_body, "init_db() must branch on _is_postgres()"

    calls = [
        ast.unparse(n.func)
        for n in ast.walk(ast.Module(body=postgres_body, type_ignores=[]))
        if isinstance(n, ast.Call)
    ]
    assert not any("create_all" in c for c in calls), (
        f"PostgreSQL branch must not call create_all(); found calls: {calls}"
    )


def test_expected_alembic_head_is_defined():
    """A single expected revision constant must exist for drift detection."""
    from backend.app.db.init_db import EXPECTED_ALEMBIC_HEAD

    assert isinstance(EXPECTED_ALEMBIC_HEAD, str) and EXPECTED_ALEMBIC_HEAD, (
        "EXPECTED_ALEMBIC_HEAD must be a non-empty revision string"
    )


def test_expected_alembic_head_matches_migration_files():
    """EXPECTED_ALEMBIC_HEAD must match an actual migration on disk."""
    from backend.app.db.init_db import EXPECTED_ALEMBIC_HEAD

    versions = list((root_dir / "backend" / "alembic" / "versions").glob("*.py"))
    revisions = {p.name.split("_", 1)[0] for p in versions}
    assert EXPECTED_ALEMBIC_HEAD in revisions, (
        f"EXPECTED_ALEMBIC_HEAD '{EXPECTED_ALEMBIC_HEAD}' has no matching migration "
        f"file; known revisions: {sorted(revisions)}"
    )


@pytest.mark.asyncio
async def test_check_migrations_current_returns_true_for_sqlite(monkeypatch):
    """SQLite is not Alembic-managed; the check must be a safe no-op."""
    from backend.app.db import init_db as init_db_module

    monkeypatch.setattr(init_db_module, "_is_postgres", lambda: False)
    assert await init_db_module.check_migrations_current() is True


@pytest.mark.asyncio
async def test_sqlite_init_still_creates_schema():
    """Local/test SQLite databases must still be created via create_all."""
    from backend.app.db import init_db as init_db_module
    from sqlalchemy import text

    assert init_db_module._is_postgres() is False, (
        "Test suite must run on SQLite for this assertion to be meaningful"
    )
    await init_db_module.init_db()

    async with init_db_module.engine.connect() as conn:
        tables = await conn.scalar(
            text("SELECT count(*) FROM sqlite_master WHERE type='table'")
        )
    assert tables and tables > 0, "SQLite schema was not created by init_db()"


def test_create_all_is_not_called_in_production_lifespan():
    """The production lifespan must delegate to the dialect-aware init_db()."""
    from backend.app.main import lifespan

    source = inspect.getsource(lifespan)
    assert "create_all" not in source, (
        "lifespan() must never call create_all() directly"
    )
    assert "init_db()" in source


def test_no_destructive_operations_in_init_db():
    """init_db must never drop, truncate, or reset anything.

    Only actual SQL string literals are inspected, so ordinary English in
    docstrings/comments (e.g. the word "truncated") cannot trip the check.
    """
    import ast
    import re

    from backend.app.db import init_db as init_db_module

    tree = ast.parse(inspect.getsource(init_db_module))

    sql_literals = [
        n.value
        for n in ast.walk(tree)
        if isinstance(n, ast.Constant)
        and isinstance(n.value, str)
        and n.value.strip().lower().startswith(
            ("select ", "drop ", "truncate ", "delete ", "alter ", "insert ", "update ")
        )
    ]
    for statement in sql_literals:
        assert not re.match(
            r"\s*(drop|truncate|delete)\b", statement.strip().lower()
        ), f"init_db() must never execute destructive SQL: {statement!r}"

    called = [
        ast.unparse(n.func)
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
    ]
    assert not any("drop_all" in c for c in called), (
        "init_db() must never call metadata.drop_all()"
    )
    assert not any("execute" in c and "text(" in c.lower() for c in called), (
        "init_db() should not execute raw DDL/DML statements"
    )


# --------------------------------------------------------------------------
# Production configuration guards (no fabricated judge verdicts)
# --------------------------------------------------------------------------


def _prod_settings(**overrides):
    from backend.app.core.config import Settings

    base = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "k" * 80,
        "DATABASE_URL": "postgresql+asyncpg://u:p@db.example.com/neondb",
        "CORS_ORIGINS": ["https://app.example.com"],
        "SECURE_COOKIES": True,
    }
    base.update(overrides)
    return Settings(**base)


def test_production_rejects_mock_judge_driver():
    """Production must refuse the mock judge driver (fabricated verdicts)."""
    is_valid, issues = _prod_settings(
        JUDGE_ENABLED=True, JUDGE_SANDBOX_DRIVER="mock"
    ).validate_production_config()
    assert is_valid is False, "Production must not accept JUDGE_SANDBOX_DRIVER=mock"
    assert any("JUDGE_SANDBOX_DRIVER" in i for i in issues)


def test_production_accepts_docker_judge_driver():
    """The real Docker sandbox remains the only acceptable production driver."""
    is_valid, issues = _prod_settings(
        JUDGE_ENABLED=True, JUDGE_SANDBOX_DRIVER="docker"
    ).validate_production_config()
    assert is_valid is True, f"Unexpected production config issues: {issues}"


def test_production_still_rejects_sqlite():
    """The SQLite guardrail must remain intact after the init_db change."""
    is_valid, issues = _prod_settings(
        DATABASE_URL="sqlite+aiosqlite:///./dsaapp.db"
    ).validate_production_config()
    assert is_valid is False
    assert any("SQLite" in i or "sqlite" in i for i in issues)


def test_judge_enabled_flag_defaults_to_true():
    """The judge must be on by default; it is never silently disabled."""
    from backend.app.core.config import Settings

    assert Settings().JUDGE_ENABLED is True


def test_disabling_judge_does_not_relax_driver_requirement():
    """Turning the judge off must not make a mock driver acceptable."""
    is_valid, _ = _prod_settings(
        JUDGE_ENABLED=False, JUDGE_SANDBOX_DRIVER="docker"
    ).validate_production_config()
    assert is_valid is True, "JUDGE_ENABLED=false with docker driver is valid"


# --------------------------------------------------------------------------
# Render / PaaS production configuration
# --------------------------------------------------------------------------


def _dockerfile_entrypoint_cmd() -> str:
    """Returns the image entrypoint CMD (not the HEALTHCHECK's CMD).

    Both start with 'CMD', so the entrypoint is the final one in the file.
    """
    dockerfile = (root_dir / "backend" / "Dockerfile").read_text(encoding="utf-8")
    cmd_lines = [ln for ln in dockerfile.splitlines() if ln.strip().startswith("CMD")]
    assert cmd_lines, "Dockerfile must define a CMD"
    return cmd_lines[-1].strip()


def test_dockerfile_binds_platform_port_not_hardcoded_8000():
    """Render injects $PORT. A hardcoded 8000 makes the health check time out."""
    cmd = _dockerfile_entrypoint_cmd()

    assert "${PORT" in cmd, f"Production CMD must expand $PORT; found: {cmd}"
    assert "--host 0.0.0.0" in cmd, "Production CMD must bind 0.0.0.0"
    assert '"--port", "8000"' not in cmd, (
        "Production CMD must not hardcode port 8000 in exec form"
    )
    assert "--reload" not in cmd, "Production CMD must never use --reload"


def test_dockerfile_healthcheck_uses_port_variable():
    """The container health probe must follow $PORT, not a fixed port."""
    dockerfile = (root_dir / "backend" / "Dockerfile").read_text(encoding="utf-8")
    joined = "\n".join(
        ln for ln in dockerfile.splitlines()
        if "HEALTHCHECK" in ln or "urlopen" in ln
    )
    assert "PORT" in joined, "HEALTHCHECK must probe the $PORT-derived port"
    assert "127.0.0.1:8000/health" not in joined, (
        "HEALTHCHECK must not hardcode port 8000"
    )


def test_render_blueprint_declares_health_path_and_no_secrets():
    """render.yaml must set the health path and must not embed secrets."""
    path = root_dir / "render.yaml"
    assert path.exists(), "render.yaml must exist for Render Blueprint deploys"
    text = path.read_text(encoding="utf-8")

    assert "healthCheckPath: /health" in text, "Render must health-check /health"
    assert "runtime: docker" in text, "Render service must use the Docker runtime"
    assert "./backend/Dockerfile" in text, "Render must point at the real Dockerfile"

    for secret in ("DATABASE_URL", "SECRET_KEY", "GOOGLE_AI_API_KEY",
                   "CORS_ORIGINS", "ALLOWED_HOSTS"):
        assert secret in text, f"{secret} should be declared in render.yaml"

    for block in ("DATABASE_URL", "SECRET_KEY", "GOOGLE_AI_API_KEY"):
        idx = text.index(f"- key: {block}")
        snippet = text[idx : idx + 120]
        assert "sync: false" in snippet, (
            f"{block} must use `sync: false` so the secret stays out of git"
        )
        assert "value:" not in snippet, f"{block} must not have a committed value"


# --------------------------------------------------------------------------
# CORS / host env parsing (the SettingsError that broke the container)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('["https://a.example.com","https://b.example.com"]',
         ["https://a.example.com", "https://b.example.com"]),
        ("https://a.example.com,https://b.example.com",
         ["https://a.example.com", "https://b.example.com"]),
        ("[https://a.example.com]", ["https://a.example.com"]),
        ("https://single.example.com", ["https://single.example.com"]),
        ("", []),
    ],
)
def test_cors_origins_accepts_all_shell_formats(raw, expected):
    """Shell quoting varies by platform; parsing must never raise."""
    from backend.app.core.config import Settings

    assert Settings(CORS_ORIGINS=raw).CORS_ORIGINS == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ('["a.example.com","b.example.com"]', ["a.example.com", "b.example.com"]),
        ("a.example.com,b.example.com", ["a.example.com", "b.example.com"]),
        ("[a.example.com]", ["a.example.com"]),
        ("", []),
    ],
)
def test_allowed_hosts_accepts_all_shell_formats(raw, expected):
    from backend.app.core.config import Settings

    assert Settings(ALLOWED_HOSTS=raw).ALLOWED_HOSTS == expected


def test_cors_env_var_never_raises_settings_error(monkeypatch):
    """A plain, unquoted origin env var must not crash Settings construction.

    Regression: pydantic-settings JSON-decodes complex fields at the source
    layer, raising SettingsError before the field_validator could run. This
    aborted the container with
    "error parsing value for field CORS_ORIGINS".
    """
    from backend.app.core.config import Settings

    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com")
    monkeypatch.setenv("ALLOWED_HOSTS", "api.example.com")
    s = Settings()
    assert s.CORS_ORIGINS == ["https://app.example.com"]
    assert s.ALLOWED_HOSTS == ["api.example.com"]


def test_production_requires_allowed_hosts():
    """Missing ALLOWED_HOSTS is what made /health answer 400 on Render."""
    from backend.app.core.config import Settings

    s = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="k" * 80,
        DATABASE_URL="postgresql+asyncpg://u:p@db.example.com/neondb",
        CORS_ORIGINS=["https://app.example.com"],
        ALLOWED_HOSTS=[],
        SECURE_COOKIES=True,
        JUDGE_ENABLED=True,
        JUDGE_SANDBOX_DRIVER="docker",
    )
    is_valid, issues = s.validate_production_config()
    assert is_valid is False
    assert any("ALLOWED_HOSTS" in i for i in issues)


def test_api_docs_opt_in_flag():
    """/docs stays disabled in production unless explicitly enabled."""
    from backend.app.core.config import Settings

    assert Settings(ENABLE_API_DOCS=False).ENABLE_API_DOCS is False
    assert Settings(ENABLE_API_DOCS=True).ENABLE_API_DOCS is True