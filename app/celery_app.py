from __future__ import annotations

from datetime import timedelta

from celery import Celery

from .settings import Settings, get_settings

settings: Settings = get_settings()

celery = Celery(
    "synergyway_tasks",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.users",
        "app.tasks.addresses",
        "app.tasks.credit_cards",
    ],
)

# Celery config: reliability-friendly defaults
celery.conf.task_acks_late = True
celery.conf.worker_prefetch_multiplier = 1
celery.conf.task_serializer = "json"
celery.conf.accept_content = ["json"]
celery.conf.result_serializer = "json"
celery.conf.timezone = "UTC"

# Beat schedule built from human-friendly env values (e.g. "15m", "1h", "30s")
celery.conf.beat_schedule = {
    "sync-users": {
        "task": "app.tasks.users.sync_users",
        "schedule": timedelta(seconds=Settings.parse_duration(settings.users_every)),
    },
    "enrich-addresses": {
        "task": "app.tasks.addresses.enrich_missing_addresses",
        "schedule": timedelta(seconds=Settings.parse_duration(settings.enrich_addr_every)),
        "args": (settings.batch_size,),
    },
    "enrich-cards": {
        "task": "app.tasks.credit_cards.enrich_missing_cards",
        "schedule": timedelta(seconds=Settings.parse_duration(settings.enrich_card_every)),
        "args": (settings.batch_size,),
    },
}
