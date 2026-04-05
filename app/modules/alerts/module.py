from fastapi import APIRouter


class Module:
    name = "alerts"

    def register_routes(self) -> APIRouter:
        return APIRouter(tags=["alerts"])

    def register_tasks(self) -> list[object]:
        return []
