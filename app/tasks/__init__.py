from __future__ import annotations

from datetime import timedelta

from app.celery_app import celery
from app.settings import get_settings

settings = get_settings()

celery.conf.beat_schedule = {
    "sync-users": {
        "task": "app.tasks.users.sync_users",
        "schedule": timedelta(seconds=settings.parse_duration(settings.users_every)),
    },
    "enrich-missing-addresses": {
        "task": "app.tasks.addresses.enrich_missing_addresses",
        "schedule": timedelta(seconds=settings.parse_duration(settings.enrich_addr_every)),
    },
    "enrich-missing-cards": {
        "task": "app.tasks.credit_cards.enrich_missing_cards",
        "schedule": timedelta(seconds=settings.parse_duration(settings.enrich_card_every)),
    },
}
