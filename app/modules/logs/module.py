from fastapi import APIRouter

from app.modules.logs.jobs import start_log_pipeline_job


class Module:
    name = "logs"

    def register_routes(self) -> APIRouter:
        from app.modules.logs.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [start_log_pipeline_job]
