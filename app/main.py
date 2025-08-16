from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import routes_users

from .db import engine
from .logging_config import setup_logging
from .models import Base

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context for startup/shutdown events.
    Here we create DB tables on startup.
    """
    # startup
    Base.metadata.create_all(bind=engine)
    logger.info("db_tables_created")
    yield
    # shutdown (if you ever need to close sessions, cleanup, etc.)
    logger.info("app_shutdown")


app = FastAPI(
    title="SynergyWay Celery Test",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Simple health check endpoint."""
    logger.info("health_check")
    return {"status": "ok"}


# Routers
app.include_router(routes_users.router)
