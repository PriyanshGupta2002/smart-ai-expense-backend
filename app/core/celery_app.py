from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "expense_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.receipt_tasks",
        "app.tasks.gmail_tasks",
        "app.tasks.gmail_scheduler_tasks",
    ],
)


celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


celery_app.conf.beat_schedule = {
    "sync-gmail-every-5-minutes": {
        "task": "app.tasks.gmail_scheduler_tasks.schedule_gmail_syncs",
        "schedule": 300.0,
    },
}
