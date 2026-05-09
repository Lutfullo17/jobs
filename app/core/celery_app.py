from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "jobify_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=True,
    task_store_errors_even_if_ignored=False,
    task_publish_retry=False,
)

celery_app.autodiscover_tasks(["app.tasks"])
