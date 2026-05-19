import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> bool:
    """
    True qaytsa so'rovga ruxsat bor.
    False qaytsa rate limit oshib ketgan.
    """
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
        return current <= limit
    except Exception:
        # Redis ishlamasa limit qo'llanmaydi — so'rov rad etiladi (xavfsizlik).
        return False
