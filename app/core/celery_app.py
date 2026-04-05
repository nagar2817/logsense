from celery import Celery

from app.core.bootstrap import bootstrap_celery_tasks
from app.core.config import Settings
from app.core.database import initialize_database


settings = Settings()
celery_app = Celery("pipeline-execution", broker=settings.redis_url, backend=settings.result_backend_url)
celery_app.conf.update(
    task_default_queue="default",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
)
initialize_database(settings=settings)
bootstrap_celery_tasks(celery_app=celery_app, settings=settings)
