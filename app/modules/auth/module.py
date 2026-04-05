from fastapi import APIRouter


class Module:
    name = "auth"

    def register_routes(self) -> APIRouter:
        from app.modules.auth.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
