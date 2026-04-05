from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.actions.services import ActionService

settings = Settings()


class StoreActionJob(BaseJob):
    name = "actions.store"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = ActionService(settings=settings)
        action = service.create_action(
            incident_id=str(payload["incident_id"]),
            title=str(payload["title"]),
            description=str(payload["description"]),
        )
        return {"message_key": "incident.action_created", "action": action.model_dump()}


job = StoreActionJob(celery_app=celery_app)


@celery_app.task(bind=True, name="actions.store")
def store_action_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
