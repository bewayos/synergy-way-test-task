from __future__ import annotations

import logging
from typing import Any

from celery import shared_task
from requests import RequestException

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def sync_users() -> dict[str, Any]:
    """
    Periodically sync users from JSONPlaceholder and upsert into DB.

    Implementation note:
    - Real HTTP/DB logic will be added next step.
    - For now we keep a reliable, testable shell and JSON-ish logs.
    """
    logger.info("sync_users.started", extra={"task": "sync_users"})
    # TODO: fetch from external API, map to models, upsert by external_id
    logger.info("sync_users.finished", extra={"task": "sync_users"})
    return {"status": "ok"}
