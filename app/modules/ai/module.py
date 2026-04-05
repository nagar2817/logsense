from fastapi import APIRouter

from app.modules.ai.jobs import ai_analysis_job


class Module:
    name = "ai"

    def register_routes(self) -> APIRouter:
        return APIRouter(tags=["ai"])

    def register_tasks(self) -> list[object]:
        return [ai_analysis_job]
