from pathlib import Path

from celery import Celery
from fastapi import APIRouter, FastAPI

from app.core.bootstrap import bootstrap_app, bootstrap_celery_tasks
from app.core.config import Settings
from app.core.database import initialize_database


class DummyModule:
    name = "dummy"

    def __init__(self) -> None:
        self.router_registered = False
        self.task_registered = False

    def register_routes(self) -> APIRouter:
        router = APIRouter()

        @router.get("/dummy")
        def dummy() -> dict[str, str]:
            return {"status": "ok"}

        self.router_registered = True
        return router

    def register_tasks(self) -> list[object]:
        self.task_registered = True

        def fake_task() -> dict[str, str]:
            return {"status": "ok"}

        fake_task.name = "dummy.task"  # type: ignore[attr-defined]
        return [fake_task]


def test_initialize_database_creates_sqlite_file(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )

    initialize_database(settings=settings)

    assert Path(settings.sqlite_database_path).exists()


def test_bootstrap_app_and_worker_register_modules(monkeypatch) -> None:
    module = DummyModule()
    settings = Settings(auto_discover_modules=False)
    app = FastAPI()
    celery = Celery("test")

    monkeypatch.setattr("app.core.bootstrap.load_modules", lambda settings: [module])

    bootstrap_app(app=app, settings=settings)
    bootstrap_celery_tasks(celery_app=celery, settings=settings)

    assert module.router_registered is True
    assert module.task_registered is True
    assert "/api/v1/dummy" in {route.path for route in app.routes}
    assert "dummy.task" in celery.tasks
