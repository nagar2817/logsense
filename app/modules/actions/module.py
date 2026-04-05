from fastapi import APIRouter

from app.modules.actions.jobs import store_action_job


class Module:
    name = "actions"

    def register_routes(self) -> APIRouter:
        from app.modules.actions.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [store_action_job]
