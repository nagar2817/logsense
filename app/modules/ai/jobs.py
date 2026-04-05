from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.ai.services import AIService
from app.modules.ai.schemas import AIAnalysisRequest

settings = Settings()


class AIAnalysisJob(BaseJob):
    name = "ai.analysis"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = AIService(settings=settings)
        request = AIAnalysisRequest(**payload["cluster"], reasons=list(payload["reasons"]))
        result = service.analyze(request)
        from app.modules.incident.jobs import create_incident_job

        create_incident_job.delay(result.model_dump())
        return {"message_key": "ai.analysis_completed", "analysis": result.model_dump()}


job = AIAnalysisJob(celery_app=celery_app)


@celery_app.task(bind=True, name="ai.analysis")
def ai_analysis_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
