import logging
from typing import Any, Dict

from fastapi import Depends, FastAPI

from . import __version__
from .db import close_pool, connection_dependency, init_pool
from .settings import settings
from .adapters.run_adapters import run_all_adapters
from .pipeline.ingest import run_ingest


logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("lead_engine")

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event() -> None:
    init_pool()
    logger.info("API startup complete", extra={"app": settings.app_name})


@app.on_event("shutdown")
async def shutdown_event() -> None:
    close_pool()
    logger.info("API shutdown complete")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "app": settings.app_name, "version": __version__}


# Simple dependency wire-up example
@app.get("/health/db")
async def health_db(conn=Depends(connection_dependency)) -> Dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        cur.fetchone()
    return {"status": "ok"}


@app.post("/debug/run_adapters")
async def debug_run_adapters() -> Dict[str, Any]:
    """
    Temporary debugging endpoint to execute adapters and return ingestion summary.
    """
    summary = run_all_adapters()
    return {"run": "completed", "summary": summary}


@app.post("/run/ingest")
async def run_ingest_endpoint(conn=Depends(connection_dependency)) -> Dict[str, Any]:
    """
    Production-style ingest trigger.
    """
    return run_ingest(conn)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
