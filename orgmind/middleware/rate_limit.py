"""
令牌桶限流中间件 - 基于 Redis
"""
import time
import redis.asyncio as aioredis
from fastapi import Request, HTTPException
from orgmind.config import REDIS_URL
from orgmind.config_production import RATE_LIMIT_PER_MINUTE, RATE_LIMIT_RETRIEVE_PER_MINUTE, RATE_LIMIT_ENABLED

redis = aioredis.from_url(REDIS_URL, decode_responses=True)

ENDPOINT_LIMITS = {
    "/api/v1/retrieve": RATE_LIMIT_RETRIEVE_PER_MINUTE,
    "/api/v1/memory": 120,
    "/api/v1/agent/": 60,
}


async def rate_limit_middleware(request: Request, call_next):
    if not RATE_LIMIT_ENABLED:
        return await call_next(request)

    path = request.url.path
    limit = RATE_LIMIT_PER_MINUTE
    for prefix, lim in ENDPOINT_LIMITS.items():
        if path.startswith(prefix):
            limit = lim
            break

    client_ip = request.client.host if request.client else "unknown"
    key = f"orgmind:ratelimit:{client_ip}:{int(time.time() / 60)}"

    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, 60)
        if count > limit:
            raise HTTPException(status_code=429, detail="RATE_LIMIT_EXCEEDED")
    except HTTPException:
        raise
    except Exception:
        pass  # Redis不可用时降级放行

    return await call_next(request)
