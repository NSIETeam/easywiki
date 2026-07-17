"""
查询结果 Redis 缓存, 大幅降低重复检索的延迟
"""
import hashlib
import json
from typing import Optional, Dict, Any
import redis.asyncio as aioredis
from orgmind.config import REDIS_URL
from orgmind.config_production import QUERY_CACHE_TTL, QUERY_CACHE_ENABLED

redis = aioredis.from_url(REDIS_URL, decode_responses=True)


def _cache_key(prefix: str, **kwargs) -> str:
    raw = json.dumps(kwargs, sort_keys=True, default=str)
    return f"orgmind:{prefix}:{hashlib.md5(raw.encode()).hexdigest()[:16]}"


async def get_cached_query(prefix: str, **kwargs) -> Optional[Dict]:
    if not QUERY_CACHE_ENABLED:
        return None
    key = _cache_key(prefix, **kwargs)
    try:
        val = await redis.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


async def set_cached_query(prefix: str, result: Dict, **kwargs) -> None:
    if not QUERY_CACHE_ENABLED:
        return
    key = _cache_key(prefix, **kwargs)
    try:
        await redis.setex(key, QUERY_CACHE_TTL, json.dumps(result, default=str))
    except Exception:
        pass


async def invalidate_cache(pattern: str) -> None:
    """清除匹配pattern的所有缓存键"""
    try:
        keys = await redis.keys(f"orgmind:{pattern}*")
        if keys:
            await redis.delete(*keys)
    except Exception:
        pass
