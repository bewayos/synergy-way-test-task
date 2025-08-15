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
def enrich_missing_addresses(batch_size: int | None = None) -> dict[str, Any]:
    """
    Attach 1:1 addresses to users missing one (random-data-api).
    """
    logger.info(
        "enrich_missing_addresses.started",
        extra={"task": "enrich_missing_addresses", "batch_size": batch_size},
    )
    # TODO: select users without address (limit=batch_size), fetch, upsert by user_id
    logger.info("enrich_missing_addresses.finished", extra={"task": "enrich_missing_addresses"})
    return {"status": "ok"}
