from fastapi import APIRouter


class Module:
    name = "health"

    def register_routes(self) -> APIRouter:
        from app.modules.health.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
