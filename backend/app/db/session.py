"""Asynchronous database engine, session factory, and dependency injection."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import settings
from backend.app.core.logging import logger


from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def resolve_database_url_and_args(raw_url: str) -> tuple[str, dict]:
    """Resolves database URL and dialect-specific engine parameters."""
    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {
        "echo": settings.DATABASE_ECHO,
        "future": True,
    }

    if "sqlite" in raw_url:
        # SQLite specific flags
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
        return raw_url, engine_kwargs

    # PostgreSQL configuration with asyncpg
    parsed = urlsplit(raw_url)
    scheme = parsed.scheme
    if scheme in ("postgresql", "postgres", "postgresql+psycopg"):
        scheme = "postgresql+asyncpg"

    query_params = dict(parse_qsl(parsed.query))
    sslmode = query_params.pop("sslmode", None)
    query_params.pop("channel_binding", None)

    if (
        sslmode in ("require", "verify-ca", "verify-full")
        or "ssl" in query_params
        or (
            parsed.hostname
            and not parsed.hostname.startswith("127.")
            and parsed.hostname not in ("localhost", "postgres")
        )
    ):
        connect_args["ssl"] = "require"

    clean_query = urlencode(query_params)
    clean_url = urlunsplit(
        (scheme, parsed.netloc, parsed.path, clean_query, parsed.fragment)
    )

    # PostgreSQL production connection pooling settings
    engine_kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
    engine_kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = settings.DATABASE_POOL_RECYCLE
    engine_kwargs["pool_timeout"] = settings.DATABASE_POOL_TIMEOUT
    if connect_args:
        engine_kwargs["connect_args"] = connect_args

    return clean_url, engine_kwargs


def build_engine_args() -> dict:
    """Configures database connection parameters based on dialect."""
    _, kwargs = resolve_database_url_and_args(settings.DATABASE_URL)
    return kwargs


_db_url, _engine_args = resolve_database_url_and_args(settings.DATABASE_URL)

# Asynchronous engine instance
engine: AsyncEngine = create_async_engine(
    _db_url,
    **_engine_args,
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

    Ensures safe lifecycle management and automatic rollback
    on unhandled exceptions.
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
