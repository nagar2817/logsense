from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.incident.services import IncidentService

settings = Settings()


class CreateIncidentJob(BaseJob):
    name = "incident.create"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = IncidentService(settings=settings)
        incident = service.create_incident(
            fingerprint=str(payload["fingerprint"]),
            title=str(payload["title"]),
            severity=str(payload["severity"]),
            root_cause=str(payload["root_cause"]),
            suggested_action=str(payload["suggested_action"]),
        )
        from app.modules.actions.jobs import store_action_job

        store_action_job.delay(
            {
                "incident_id": incident.id,
                "title": incident.title,
                "description": incident.suggested_action,
            }
        )
        return {"message_key": "incident.created", "incident": incident.model_dump()}


job = CreateIncidentJob(celery_app=celery_app)


@celery_app.task(bind=True, name="incident.create")
def create_incident_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
