from fastapi import APIRouter

from app.modules.email.jobs import send_email_job


class Module:
    name = "email"

    def register_routes(self) -> APIRouter:
        from app.modules.email.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [send_email_job]
