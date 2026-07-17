"""
EasyWiki FastAPI entry point (production / cloud deployment)
Supports PostgreSQL + Redis via config.py and the async database layer.
"""
import signal
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from orgmind.auth.middleware import rls_middleware
from orgmind.middleware.rate_limit import rate_limit_middleware
from orgmind.middleware.metrics import metrics_middleware, render_prometheus_metrics, get_metrics
from orgmind.middleware.health import full_health_check, HealthStatus
from orgmind.middleware.logging import setup_logging, logger
from orgmind.api.routes import router as api_router
from orgmind.easywiki.routes import router as easywiki_router
from orgmind.config_production import LOG_LEVEL, GRACEFUL_SHUTDOWN_TIMEOUT


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(LOG_LEVEL)
    logger.info("EasyWiki starting", extra={"extra_fields": {"event": "startup"}})

    try:
        from orgmind.graph.engine import get_graph_engine
        get_graph_engine()
        logger.info("Graph engine initialized", extra={"extra_fields": {"event": "graph_init"}})
    except Exception:
        logger.warning("Graph engine unavailable", extra={"extra_fields": {"event": "graph_skip"}})

    yield

    logger.info("EasyWiki shutting down", extra={"extra_fields": {"event": "shutdown"}})
    await asyncio.sleep(GRACEFUL_SHUTDOWN_TIMEOUT)


app = FastAPI(
    title="EasyWiki — Agent-Driven Knowledge Management",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware order: CORS -> RLS -> RateLimit -> Metrics
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rls_middleware_wrapper(request: Request, call_next):
    return await rls_middleware(request, call_next)


@app.middleware("http")
async def rate_limit_middleware_wrapper(request: Request, call_next):
    return await rate_limit_middleware(request, call_next)


@app.middleware("http")
async def metrics_middleware_wrapper(request: Request, call_next):
    return await metrics_middleware(request, call_next)


@app.get("/health", tags=["ops"])
async def health() -> HealthStatus:
    return await full_health_check()


@app.get("/metrics", tags=["ops"], response_class=PlainTextResponse)
async def metrics():
    return render_prometheus_metrics()


@app.get("/ready", tags=["ops"])
async def ready():
    """Kubernetes readiness probe"""
    status = await full_health_check()
    if status.status == "unhealthy":
        return PlainTextResponse(status_code=503, content="not ready")
    return {"status": "ready"}


# Mount both API sets
app.include_router(api_router)                        # /api/v1/* (OrgMind legacy + session/agent/memory)
app.include_router(easywiki_router, prefix="/api/v1/easywiki")  # /api/v1/easywiki/* (EasyWiki core)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orgmind.main:app", host="0.0.0.0", port=8080, reload=True)
