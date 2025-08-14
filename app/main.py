from __future__ import annotations

import logging

from fastapi import FastAPI

from .logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="SynergyWay Celery Test", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Simple health check endpoint."""
    logger.info("health_check")
    return {"status": "ok"}
