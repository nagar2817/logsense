from fastapi import APIRouter


class Module:
    name = "system"

    def register_routes(self) -> APIRouter:
        from app.modules.system.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
