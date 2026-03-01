from typing import AsyncGenerator
import redis.asyncio as aioredis
import structlog
from app.config import get_settings

logger = structlog.get_logger()
_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


async def ping_redis() -> bool:
    try:
        client = await get_redis()
        return await client.ping()
    except Exception as e:
        logger.warning("redis.ping_failed", error=str(e))
        return False
