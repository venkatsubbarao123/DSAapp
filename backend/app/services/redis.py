"""Redis service boundary for future caching, rate limiting, and queue integration."""

from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger


class RedisService:
    """Abstraction layer over Redis client.
    
    Provides future service hooks for caching, rate-limiting tokens, and background queues.
    In local development, Redis is optional unless REDIS_REQUIRED=true.
    """

    def __init__(self, redis_url: str = settings.REDIS_URL, required: bool = settings.REDIS_REQUIRED):
        self.redis_url = redis_url
        self.required = required
        self._client: Optional[object] = None
        self._connected = False

    async def connect(self) -> bool:
        """Attempts connection to Redis if redis-py is available."""
        try:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=2.0,
            )
            await self._client.ping()
            self._connected = True
            logger.info("Connected to Redis service successfully.")
            return True
        except ImportError:
            if self.required:
                logger.error("redis-py library is not installed, but REDIS_REQUIRED is True.")
            else:
                logger.info("redis-py not installed; Redis service disabled for local development.")
            self._connected = False
            return False
        except Exception as exc:
            if self.required:
                logger.error(f"Failed to connect to required Redis service at {self.redis_url}: {exc}")
            else:
                logger.warning(f"Optional Redis service unreachable at {self.redis_url}. Running without cache.")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Closes Redis connection."""
        if self._client and hasattr(self._client, "close"):
            try:
                await self._client.close()
            except Exception:
                pass
        self._connected = False

    async def check_health(self) -> str:
        """Reports Redis health status without raising exceptions."""
        if not self._connected:
            if not self.required:
                return "disabled"
            return "disconnected"
        try:
            if self._client and hasattr(self._client, "ping"):
                await self._client.ping()
                return "healthy"
            return "disconnected"
        except Exception:
            return "unhealthy"

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def get(self, key: str) -> Optional[str]:
        """Gets value from Redis with safe graceful fallback."""
        if self._connected and self._client and hasattr(self._client, "get"):
            try:
                return await self._client.get(key)
            except Exception:
                return None
        return None

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        """Sets value in Redis with optional TTL and safe graceful fallback."""
        if self._connected and self._client and hasattr(self._client, "set"):
            try:
                if ttl and hasattr(self._client, "setex"):
                    await self._client.setex(key, ttl, value)
                else:
                    await self._client.set(key, value)
                return True
            except Exception:
                return False
        return False

    async def delete(self, key: str) -> bool:
        """Deletes key from Redis with safe graceful fallback."""
        if self._connected and self._client and hasattr(self._client, "delete"):
            try:
                await self._client.delete(key)
                return True
            except Exception:
                return False
        return False


redis_service = RedisService()


def get_redis_service() -> RedisService:
    """FastAPI dependency for accessing the Redis service."""
    return redis_service
