"""Redis service boundary for caching, rate limiting, and queue integration.

Provides resilient Redis client with namespacing, TTL enforcement,
and safe in-memory fallback when Redis is offline or running in test mode.
"""

import time

from backend.app.core.config import settings
from backend.app.core.logging import logger

DEFAULT_CACHE_TTL = 300  # 5 minutes
DEFAULT_RATELIMIT_TTL = 60  # 1 minute
DEFAULT_SESSION_TTL = 86400  # 24 hours


class RedisService:
    """Abstraction layer over Redis client with graceful in-memory fallback.

    Provides key namespacing (dsaapp:{namespace}:{key}) and prevents
    system outages if Redis becomes temporarily unreachable.
    """

    def __init__(
        self,
        redis_url: str = settings.REDIS_URL,
        required: bool = settings.REDIS_REQUIRED,
    ):
        self.redis_url = redis_url
        self.required = required
        self._client: object | None = None
        self._connected = False
        # In-memory fallback dictionary: key -> (value, expiry_timestamp_or_none)
        self._memory_fallback: dict[str, tuple[str, float | None]] = {}

    def make_key(self, namespace: str, identifier: str) -> str:
        """Constructs standardized namespaced Redis key.

        Format: dsaapp:<namespace>:<identifier>
        """
        clean_ns = namespace.strip().replace(" ", "_")
        clean_id = identifier.strip().replace(" ", "_")
        return f"dsaapp:{clean_ns}:{clean_id}"

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
                logger.error(
                    "redis-py library is not installed, but REDIS_REQUIRED is True."
                )
            else:
                logger.info(
                    "redis-py not installed; Redis service using safe in-memory fallback."
                )
            self._connected = False
            return False
        except Exception as exc:
            if self.required:
                logger.error(
                    f"Failed to connect to required Redis service at {self.redis_url}: {exc}"
                )
            else:
                logger.warning(
                    f"Optional Redis service unreachable at {self.redis_url}. Using safe in-memory fallback."
                )
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Closes Redis connection cleanly."""
        if self._client and hasattr(self._client, "close"):
            try:
                await self._client.close()
            except Exception:
                pass
        self._connected = False
        self._memory_fallback.clear()

    async def check_health(self) -> str:
        """Reports Redis health status without raising exceptions."""
        if not self._connected:
            if not self.required:
                return "disabled (in-memory fallback active)"
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

    async def get(self, key: str) -> str | None:
        """Gets value from Redis with safe in-memory fallback."""
        if self._connected and self._client and hasattr(self._client, "get"):
            try:
                return await self._client.get(key)
            except Exception as e:
                logger.warning(
                    f"Redis get failed for key {key}: {e}. Checking in-memory fallback."
                )

        # Check in-memory fallback
        if key in self._memory_fallback:
            val, expiry = self._memory_fallback[key]
            if expiry is None or expiry > time.time():
                return val
            else:
                del self._memory_fallback[key]
        return None

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Sets value in Redis with optional TTL and safe in-memory fallback."""
        if self._connected and self._client and hasattr(self._client, "set"):
            try:
                if ttl and hasattr(self._client, "setex"):
                    await self._client.setex(key, ttl, value)
                else:
                    await self._client.set(key, value)
                return True
            except Exception as e:
                logger.warning(
                    f"Redis set failed for key {key}: {e}. Storing in memory fallback."
                )

        # Store in in-memory fallback
        expiry = (time.time() + ttl) if ttl else None
        self._memory_fallback[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        """Deletes key from Redis and in-memory fallback."""
        success = False
        if self._connected and self._client and hasattr(self._client, "delete"):
            try:
                await self._client.delete(key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete failed for key {key}: {e}.")

        if key in self._memory_fallback:
            del self._memory_fallback[key]
            success = True
        return success


redis_service = RedisService()


def get_redis_service() -> RedisService:
    """FastAPI dependency for accessing the Redis service."""
    return redis_service
