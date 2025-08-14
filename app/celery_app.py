from __future__ import annotations

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
