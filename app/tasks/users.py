from __future__ import annotations

import logging
from typing import Any, Dict

from celery import shared_task
from requests import RequestException
from sqlalchemy.dialects.postgresql import insert

from app.clients.dummyjson import DummyJSONClient
from app.db import session_scope
from app.models import User
from app.settings import get_settings

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def sync_users() -> Dict[str, Any]:
    """
    Periodically sync users from DummyJSON and upsert into DB.
    Idempotent by users.external_id UNIQUE.
    """
    settings = get_settings()
    client = DummyJSONClient.from_settings(settings)

    logger.info("sync_users.started", extra={"task": "sync_users"})

    limit = 100
    skip = 0
    total_synced = 0

    while True:
        payload, total = client.list_users(limit=limit, skip=skip)
        if not payload:
            break

        with session_scope() as s:
            for u in payload:
                mapped = client.map_user(u)
                stmt = (
                    insert(User)
                    .values(**mapped)
                    .on_conflict_do_update(
                        index_elements=[User.external_id],
                        set_={k: mapped[k] for k in mapped if k != "external_id"},
                    )
                )
                s.execute(stmt)
                total_synced += 1

        skip += limit
        if skip >= total:
            break

    logger.info("sync_users.finished", extra={"synced": total_synced})
    return {"status": "ok", "synced": total_synced}
