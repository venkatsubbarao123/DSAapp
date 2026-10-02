"""Database initialization routines.

IMPORTANT (production safety)
-----------------------------
`Base.metadata.create_all()` issues a bare ``CREATE TYPE`` for every native
PostgreSQL enum declared on the models. On a database where those types already
exist (i.e. any database managed by Alembic) it raises:

    UniqueViolationError: duplicate key value violates unique constraint
    "pg_type_typname_nsp_index"  /  type "contentlevel" already exists

That aborts application startup. It is also simply the wrong tool for
production, because Alembic is the single source of truth for schema.

Therefore:
  * PostgreSQL (production)  -> NEVER run create_all. Schema is owned by
                                `alembic upgrade head`, and we only *verify*
                                that migrations are current.
  * SQLite (local dev/test)  -> create_all is retained, because it is how the
                                throwaway in-memory/file test database is
                                built. SQLite has no native enum types.

No production data is ever dropped, truncated, or reset.
"""

import backend.app.models  # noqa: F401 - Register models with Base.metadata
from sqlalchemy import text

from backend.app.core.logging import logger
from backend.app.db.base import Base
from backend.app.db.session import engine

# Alembic revision this application expects the database to be at.
# Bump this whenever a new migration is added to backend/alembic/versions/.
EXPECTED_ALEMBIC_HEAD = "7c139d4e5f6a"


def _is_postgres() -> bool:
    """True when the configured engine is PostgreSQL."""
    return engine.dialect.name in ("postgresql", "postgres")


async def check_migrations_current() -> bool:
    """Verifies the database schema is at the expected Alembic revision.

    Read-only: this never mutates the schema. Returns True when the
    ``alembic_version`` table reports the expected head, False when the table
    is absent or reports a different revision.
    """
    if not _is_postgres():
        return True

    try:
        async with engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT to_regclass('public.alembic_version')")
            )
            if not exists:
                logger.warning(
                    "Alembic version table 'alembic_version' is absent. "
                    "Run 'alembic -c alembic.ini upgrade head' before serving traffic."
                )
                return False

            current = await conn.scalar(text("SELECT version_num FROM alembic_version"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Unable to verify Alembic revision state: {exc}")
        return False

    if current != EXPECTED_ALEMBIC_HEAD:
        logger.warning(
            f"Database schema is at Alembic revision '{current}' but this build expects "
            f"'{EXPECTED_ALEMBIC_HEAD}'. Run 'alembic -c alembic.ini upgrade head'."
        )
        return False

    logger.info(f"Database schema verified at Alembic revision {current}.")
    return True


async def init_db() -> None:
    """Prepares the database schema at application startup.

    Behaviour is dialect-aware so production PostgreSQL is never touched by
    ``create_all`` (see module docstring):

    * PostgreSQL -> verify the Alembic revision only. No DDL is emitted.
    * SQLite     -> create tables for local development / throwaway test DBs.
    """
    if _is_postgres():
        logger.info(
            "PostgreSQL detected: skipping create_all(). Schema is managed by Alembic."
        )
        await check_migrations_current()
        return

    logger.info("Initializing SQLite schema via create_all()...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("SQLite database schema initialized successfully.")
