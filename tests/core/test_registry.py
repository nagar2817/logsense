from types import SimpleNamespace

from fastapi import APIRouter
from fastapi import FastAPI

from app.core.bootstrap import bootstrap_app
from app.core.config import Settings
from app.core.registry import ModuleRegistry


class DummyModule:
    def __init__(self, name: str) -> None:
        self.name = name
        self.task_registered = False

    def register_routes(self) -> APIRouter:
        router = APIRouter()

        @router.get("/status")
        def status() -> dict[str, str]:
            return {"status": self.name}

        return router

    def register_tasks(self) -> list[object]:
        self.task_registered = True
        return []


def test_registry_loads_configured_and_discovered_modules(monkeypatch) -> None:
    registry = ModuleRegistry(
        settings=Settings(enabled_modules=["app.modules.health.module"], auto_discover_modules=True)
    )
    monkeypatch.setattr(registry, "_discover_modules", lambda: ["app.modules.system.module"])
    monkeypatch.setattr(registry, "_load_from_path", lambda path: DummyModule(path.split(".")[-2]))

    loaded = registry.load_modules()

    assert [module.name for module in loaded] == ["health", "system"]


def test_registry_load_from_path_instantiates_module(monkeypatch) -> None:
    registry = ModuleRegistry(settings=Settings(auto_discover_modules=False))
    monkeypatch.setattr("app.core.registry.import_module", lambda path: SimpleNamespace(Module=lambda: DummyModule("health")))

    loaded = registry._load_from_path("app.modules.health.module")

    assert loaded.name == "health"


def test_bootstrap_app_registers_routes_and_tasks(monkeypatch) -> None:
    app = FastAPI()
    settings = Settings(auto_discover_modules=False)
    module = DummyModule("health")
    monkeypatch.setattr(ModuleRegistry, "load_modules", lambda self: [module])

    modules = bootstrap_app(app=app, settings=settings)

    assert modules == [module]
    assert module.task_registered is True
    assert "/api/v1/status" in {route.path for route in app.routes}
