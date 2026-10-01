"""Database initialization routines."""

from backend.app.core.logging import logger
from backend.app.db.base import Base
from backend.app.db.session import engine
import backend.app.models  # noqa: F401 - Register models with Base.metadata


async def init_db() -> None:
    """Creates database schema if it doesn't already exist.

    In production, Alembic migrations should be preferred over create_all.
    """
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
