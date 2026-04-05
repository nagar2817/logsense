from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.modules.email.services import EmailService


class SendEmailJob(BaseJob):
    name = "email.send"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return EmailService().send_email(payload)


job = SendEmailJob(celery_app=celery_app)


@celery_app.task(
    bind=True,
    name="email.send",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def send_email_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
