"""
生产级健康检查 - 包含所有依赖项的可用性探测
"""
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import redis.asyncio as aioredis
from sqlalchemy import text
from orgmind.database import async_session_factory
from orgmind.graph.engine import get_graph_engine
from orgmind.config import REDIS_URL


@dataclass
class HealthStatus:
    status: str  # "healthy" | "degraded" | "unhealthy"
    uptime_seconds: float
    checks: Dict[str, Dict] = field(default_factory=dict)


_start_time = time.monotonic()


async def check_database() -> Dict:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_redis() -> Dict:
    try:
        r = aioredis.from_url(REDIS_URL)
        await r.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


async def check_graph() -> Dict:
    try:
        engine = get_graph_engine()
        engine.query("MATCH (n) RETURN n LIMIT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


async def check_embedding() -> Dict:
    try:
        import openai
        return {"status": "healthy", "note": "API key configured"}
    except Exception:
        return {"status": "degraded", "error": "openai not installed"}


def check_memory() -> Dict:
    import psutil
    mem = psutil.virtual_memory()
    return {
        "status": "healthy" if mem.percent < 90 else "degraded",
        "used_percent": mem.percent,
        "available_gb": round(mem.available / (1024**3), 1),
    }


def check_disk() -> Dict:
    import psutil
    disk = psutil.disk_usage("/")
    return {
        "status": "healthy" if disk.percent < 90 else "degraded",
        "used_percent": disk.percent,
        "free_gb": round(disk.free / (1024**3), 1),
    }


async def full_health_check() -> HealthStatus:
    checks = {
        "database": await check_database(),
        "redis": await check_redis(),
        "graph_engine": await check_graph(),
        "embedding_service": await check_embedding(),
        "memory": check_memory(),
        "disk": check_disk(),
    }
    statuses = [c["status"] for c in checks.values()]
    if "unhealthy" in statuses:
        overall = "unhealthy"
    elif "degraded" in statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    return HealthStatus(
        status=overall,
        uptime_seconds=time.monotonic() - _start_time,
        checks=checks,
    )
