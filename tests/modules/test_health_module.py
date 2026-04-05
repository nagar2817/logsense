import logging
import sys
from types import ModuleType, SimpleNamespace

from celery import Celery
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.base_job import BaseJob
from app.core.bootstrap import bootstrap_app
from app.core.config import Settings
from app.core.exceptions.domain import ExternalServiceException
from app.core.exceptions.http import NotFoundException
from app.core.logging import configure_logging
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.registry import ModuleRegistry
from app.core.responses.errors import error_response
from app.main import create_app
from app.modules.health.module import Module as HealthModule
from app.modules.health.api import router as health_router
from app.modules.system.api import router as system_router
from app.utils.context import clear_request_context, get_request_context, set_request_context


def build_module_test_client() -> TestClient:
    app = FastAPI()
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")
    return TestClient(app)


def test_health_endpoint() -> None:
    client = build_module_test_client()
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["message_key"] == "health.ok"


def test_ready_endpoint() -> None:
    client = build_module_test_client()
    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["data"]["redis"] == "up"


def test_health_module_contract_and_core_smoke() -> None:
    module = HealthModule()
    assert module.name == "health"
    assert module.register_tasks() == []
    assert isinstance(module.register_routes(), APIRouter)

    set_request_context(request_id="req-1", correlation_id="corr-1")
    assert get_request_context() == {"request_id": "req-1", "correlation_id": "corr-1"}
    clear_request_context()
    assert get_request_context() == {"request_id": None, "correlation_id": None}

    configure_logging()
    assert logging.getLogger().handlers[0].formatter is not None

    custom_app = FastAPI()

    @custom_app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @custom_app.get("/protected")
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    custom_app.add_middleware(RequestIDMiddleware)
    custom_app.add_middleware(LoggingMiddleware)
    custom_app.add_middleware(AuthMiddleware, settings=Settings())

    middleware_client = TestClient(custom_app)
    assert middleware_client.get("/health").status_code == 200
    unauthorized = middleware_client.get("/protected")
    assert unauthorized.status_code == 401

    error_app = FastAPI()
    register_exception_handlers(error_app)

    @error_app.get("/not-found")
    def not_found() -> None:
        raise NotFoundException(
            message="Missing",
            message_key="email.not_found",
            error_code="EMAIL_001",
        )

    @error_app.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    error_client = TestClient(error_app, raise_server_exceptions=False)
    assert error_client.get("/not-found").status_code == 404
    assert error_client.get("/boom").status_code == 500
    assert error_response(
        ExternalServiceException(
            message="down",
            message_key="system.external_failure",
            error_code="SYSTEM_999",
        )
    )["error"]["code"] == "SYSTEM_999"

    app = create_app(Settings())
    assert app.title == "pipeline-execution"

    class DummyModule:
        name = "health"

        def __init__(self) -> None:
            self.registered = False

        def register_routes(self) -> APIRouter:
            router = APIRouter()

            @router.get("/status")
            def status() -> dict[str, str]:
                return {"status": "ok"}

            return router

        def register_tasks(self) -> list[object]:
            self.registered = True
            return []

    class ModuleFromImport(DummyModule):
        pass

    boot_module = DummyModule()
    boot_app = FastAPI()
    original_load_modules = ModuleRegistry.load_modules
    ModuleRegistry.load_modules = lambda self: [boot_module]
    try:
        modules = bootstrap_app(app=boot_app, settings=Settings(auto_discover_modules=False))
    finally:
        ModuleRegistry.load_modules = original_load_modules
    assert modules == [boot_module]
    assert boot_module.registered is True
    assert "/api/v1/status" in {route.path for route in boot_app.routes}

    import app.core.registry as registry_module

    original_import_module = registry_module.import_module
    original_iter_modules = registry_module.iter_modules
    original_modules_package = sys.modules.get("app.modules")
    registry_module.import_module = lambda path: SimpleNamespace(Module=lambda: ModuleFromImport())
    registry_module.iter_modules = lambda path: [SimpleNamespace(name="health")]
    stub_modules_package = ModuleType("app.modules")
    stub_modules_package.__path__ = []  # type: ignore[attr-defined]
    sys.modules["app.modules"] = stub_modules_package
    try:
        registry = ModuleRegistry(settings=Settings(auto_discover_modules=False))
        assert registry._load_from_path("app.modules.health.module").name == "health"
        discovery_registry = ModuleRegistry(settings=Settings(auto_discover_modules=True))
        assert discovery_registry._discover_modules() == ["app.modules.health.module"]
    finally:
        registry_module.import_module = original_import_module
        registry_module.iter_modules = original_iter_modules
        if original_modules_package is None:
            sys.modules.pop("app.modules", None)
        else:
            sys.modules["app.modules"] = original_modules_package

    class DummyJob(BaseJob):
        name = "dummy.job"

        def run(self, payload: dict[str, str]) -> dict[str, str]:
            return {"status": payload["status"]}

    assert DummyJob(celery_app=Celery("test")).execute({"status": "ok"}) == {"status": "ok"}
