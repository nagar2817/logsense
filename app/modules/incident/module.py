from fastapi import APIRouter

from app.modules.incident.jobs import create_incident_job


class Module:
    name = "incident"

    def register_routes(self) -> APIRouter:
        from app.modules.incident.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [create_incident_job]
