"""Rate limiting service with Redis implementation and in-memory local fallback."""

import time
from collections import defaultdict

from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.redis import redis_service


class RateLimiter:
    """Sliding-window rate limiter protecting against brute-force and credential stuffing."""

    def __init__(self):
        # In-memory sliding window buffer: key -> list of timestamps
        self._local_buckets: dict[str, list[float]] = defaultdict(list)

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        """Enforces rate limit. Raises HTTP 429 if threshold exceeded."""
        if not settings.RATE_LIMIT_ENABLED:
            return

        now = time.time()

        # If Redis is connected, use Redis atomic sliding window
        if redis_service.is_connected and redis_service._client:
            try:
                client: any = redis_service._client
                redis_key = f"rl:{key}"
                pipe = client.pipeline()
                pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
                pipe.zadd(redis_key, {str(now): now})
                pipe.zcard(redis_key)
                pipe.expire(redis_key, window_seconds)
                results = await pipe.execute()
                request_count = results[2]

                if request_count > max_requests:
                    logger.warning(
                        f"Rate limit exceeded for key={key}: {request_count}/{max_requests}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Too many requests. Please slow down and try again later.",
                    )
                return
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning(
                    f"Redis rate limiter failed, falling back to local memory: {exc}"
                )

        # In-memory fallback
        timestamps = self._local_buckets[key]
        # Prune expired timestamps
        cutoff = now - window_seconds
        self._local_buckets[key] = [t for t in timestamps if t > cutoff]

        if len(self._local_buckets[key]) >= max_requests:
            logger.warning(
                f"Local rate limit exceeded for key={key}: {len(self._local_buckets[key])}/{max_requests}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again later.",
            )

        self._local_buckets[key].append(now)


rate_limiter = RateLimiter()
