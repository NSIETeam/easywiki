"""
EasyWiki v1.0 — Cloud Deployment Entry Point
================================================================
Usage:
    pip install -r requirements.txt
    export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/easywiki
    python -m uvicorn orgmind.main:app --host 0.0.0.0 --port 8080

Requires: PostgreSQL 14+ with pgvector extension
For development without PG, use: python -m uvicorn orgmind.main_sqlite:app
================================================================
"""
import sys
import asyncio
from contextlib import asynccontextmanager

# -- Pre-flight: PostgreSQL availability check --------------------------
try:
    import sqlalchemy  # noqa: F401
    import asyncpg   # noqa: F401
except ImportError as e:
    print(f"[EasyWiki] FATAL: Missing PostgreSQL driver: {e}")
    print("  Install: pip install sqlalchemy[asyncio] asyncpg")
    print("  Or for local dev: python -m uvicorn orgmind.main_sqlite:app")
    sys.exit(1)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from orgmind.auth.middleware import rls_middleware
from orgmind.middleware.rate_limit import rate_limit_middleware
from orgmind.middleware.metrics import metrics_middleware, render_prometheus_metrics
from orgmind.middleware.health import full_health_check, HealthStatus
from orgmind.middleware.logging import setup_logging, logger
from orgmind.api.routes import router as api_router
from orgmind.easywiki.routes import router as easywiki_router
from orgmind.config_production import LOG_LEVEL, GRACEFUL_SHUTDOWN_TIMEOUT


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(LOG_LEVEL)
    logger.info("EasyWiki starting (cloud mode)", extra={"extra_fields": {"event": "startup"}})

    try:
        from orgmind.graph.engine import get_graph_engine
        get_graph_engine()
        logger.info("Graph engine initialized", extra={"extra_fields": {"event": "graph_init"}})
    except Exception:
        logger.warning("Graph engine unavailable (non-critical)", extra={"extra_fields": {"event": "graph_skip"}})

    yield

    logger.info("EasyWiki shutting down", extra={"extra_fields": {"event": "shutdown"}})
    await asyncio.sleep(GRACEFUL_SHUTDOWN_TIMEOUT)


app = FastAPI(
    title="EasyWiki — Agent-Driven Knowledge Management",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware: CORS -> RLS -> RateLimit -> Metrics
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


# Ops endpoints
@app.get("/health", tags=["ops"])
async def health() -> HealthStatus:
    return await full_health_check()


@app.get("/metrics", tags=["ops"], response_class=PlainTextResponse)
async def metrics():
    return render_prometheus_metrics()


@app.get("/ready", tags=["ops"])
async def ready():
    status = await full_health_check()
    if status.status == "unhealthy":
        return PlainTextResponse(status_code=503, content="not ready")
    return {"status": "ready"}


# Mount API routers
app.include_router(api_router)                                    # /api/v1/* (OrgMind: memory, auth, session, agent)
app.include_router(easywiki_router, prefix="/api/v1/easywiki")   # /api/v1/easywiki/* (EasyWiki: projects, pages, inbox, graph)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("orgmind.main:app", host="0.0.0.0", port=8080, reload=True)
