"""Asynchronous database engine, session factory, and dependency injection."""

from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import settings
from backend.app.core.logging import logger


def build_engine_args() -> dict:
    """Configures database connection parameters based on dialect."""
    connect_args = {}
    engine_kwargs = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    if "sqlite" in settings.DATABASE_URL:
        # SQLite specific flags
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL production connection pooling settings
        engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE
        engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT

    return engine_kwargs


# Asynchronous engine instance
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    **build_engine_args(),
)

# Asynchronous session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection generator for database sessions.
    
    Ensures safe lifecycle management and automatic rollback on unhandled exceptions.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    """Performs a lightweight ping against the database."""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as exc:
        logger.error(f"Database health check failed: {exc}")
        return False
