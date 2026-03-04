from __future__ import annotations

from typing import Optional

import redis.asyncio as aioredis

from core.config import settings

_redis_client: Optional[aioredis.Redis] = None


def get_redis() -> aioredis.Redis:
    """Return the shared async Redis client instance."""
    if _redis_client is None:
        raise RuntimeError("Redis client has not been initialised. Call init_redis() first.")
    return _redis_client


async def init_redis() -> aioredis.Redis:
    """Create and store the global async Redis client."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    await _redis_client.ping()
    return _redis_client


async def close_redis() -> None:
    """Close the global Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
