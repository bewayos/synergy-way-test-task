from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api import routes_users

from .db import engine
from .logging_config import setup_logging
from .models import Base

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="SynergyWay Celery Test", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    """
    Initialize database tables on app startup.

    In production systems migrations (Alembic) should be used instead.
    """
    Base.metadata.create_all(bind=engine)
    logger.info("db_tables_created")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Simple health check endpoint."""
    logger.info("health_check")
    return {"status": "ok"}


app.include_router(routes_users.router)
