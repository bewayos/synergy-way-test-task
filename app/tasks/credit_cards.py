from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List

from celery import shared_task
from requests import RequestException
from sqlalchemy.dialects.postgresql import insert

from app.clients.dummyjson import DummyJSONClient
from app.db import session_scope
from app.models import CreditCard, User
from app.settings import get_settings

logger = logging.getLogger(__name__)


def _select_user_external_ids_without_card(batch_size: int | None) -> Iterable[int]:
    with session_scope() as s:
        q = (
            s.query(User.external_id)
            .outerjoin(CreditCard, CreditCard.user_id == User.id)
            .filter(CreditCard.id.is_(None))
            .order_by(User.id.asc())
        )
        if batch_size:
            q = q.limit(batch_size)
        return [row[0] for row in q.all()]


@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def enrich_missing_cards(batch_size: int | None = None) -> Dict[str, Any]:
    """
    Attach 1:1 credit cards to users missing one (DummyJSON). Idempotent.
    """
    settings = get_settings()
    client = DummyJSONClient.from_settings(settings)

    logger.info("enrich_missing_cards.started", extra={"batch_size": batch_size})
    missing: List[int] = list(_select_user_external_ids_without_card(batch_size))
    updated = 0

    for ext_id in missing:
        user_json = client.get_user(ext_id)
        mapped = client.map_credit_card(user_json)
        with session_scope() as s:
            user = s.query(User).filter_by(external_id=ext_id).first()
            if not user:
                continue
            stmt = (
                insert(CreditCard)
                .values(user_id=user.id, **mapped)
                .on_conflict_do_update(
                    index_elements=[CreditCard.user_id],
                    set_={k: mapped[k] for k in mapped if k != "user_id"},
                )
            )
            s.execute(stmt)
        updated += 1

    logger.info("enrich_missing_cards.finished", extra={"updated": updated})
    return {"status": "ok", "updated": updated}
