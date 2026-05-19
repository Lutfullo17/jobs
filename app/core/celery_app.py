import sys

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "jobify_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

_celery_conf: dict = {
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "enable_utc": True,
    "task_ignore_result": True,
    "task_store_errors_even_if_ignored": False,
    "task_publish_retry": False,
}

# Windows: prefork/spawn pool billiard bilan ishlamaydi (WinError 5/6).
if sys.platform == "win32":
    _celery_conf["worker_pool"] = "solo"

celery_app.conf.update(**_celery_conf)

# "app.tasks" emas "app" — autodiscover `app.tasks.tasks` qidiradi; bizda `email_tasks.py`.
celery_app.autodiscover_tasks(["app"])
import app.tasks.email_tasks  # noqa: F401 — workerda send_email_task ro'yxatdan o'tishi uchun
