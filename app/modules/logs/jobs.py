from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app


class StartLogPipelineJob(BaseJob):
    name = "logs.start_pipeline"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        from app.modules.analysis.jobs import cluster_logs_job

        cluster_logs_job.delay(payload)
        return {
            "message_key": "logs.ingested",
            "log_id": payload["log_id"],
            "fingerprint": payload["fingerprint"],
        }


job = StartLogPipelineJob(celery_app=celery_app)


@celery_app.task(bind=True, name="logs.start_pipeline")
def start_log_pipeline_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
