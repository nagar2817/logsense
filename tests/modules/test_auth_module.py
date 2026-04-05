import logging
import sys
from types import ModuleType, SimpleNamespace

from celery import Celery
from fastapi import APIRouter, FastAPI
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.base_job import BaseJob
from app.core.bootstrap import bootstrap_app, bootstrap_celery_tasks
from app.core.config import Settings
from app.core.exceptions.domain import ExternalServiceException
from app.core.exceptions.http import (
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.core.logging import configure_logging
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.messages.base import BaseMessageKeys
from app.core.messages.builder import build_message_key
from app.core.registry import ModuleRegistry
from app.core.responses.base import success_response
from app.core.responses.errors import error_response
from app.main import create_app
from app.modules.auth.module import Module as AuthModule
from app.modules.auth.services import AuthService
from app.modules.auth.api import router
from app.modules.health.api import router as health_router
from app.modules.health.module import Module as HealthModule
from app.modules.system.api import router as system_router
from app.modules.system.module import Module as SystemModule
from app.utils.context import clear_request_context, get_request_context, set_request_context


def test_auth_validate_endpoint() -> None:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/auth/validate")

    assert response.status_code == 200
    assert response.json()["message_key"] == "auth.valid"
    assert response.json()["data"]["authenticated"] is True

    auth_module = AuthModule()
    health_module = HealthModule()
    system_module = SystemModule()
    assert auth_module.name == "auth"
    assert health_module.name == "health"
    assert system_module.name == "system"
    assert auth_module.register_tasks() == []
    assert health_module.register_tasks() == []
    assert system_module.register_tasks() == []

    auth_service = AuthService(settings=Settings())
    assert auth_service.is_valid_api_key("local-dev-key") is True
    assert auth_service.is_valid_api_key("bad-key") is False

    set_request_context(request_id="req-1", correlation_id="corr-1")
    assert get_request_context() == {"request_id": "req-1", "correlation_id": "corr-1"}
    clear_request_context()
    assert get_request_context() == {"request_id": None, "correlation_id": None}

    configure_logging()
    assert logging.getLogger().handlers[0].formatter is not None

    module_app = FastAPI()
    module_app.include_router(health_router, prefix="/api/v1")
    module_app.include_router(system_router, prefix="/api/v1")
    module_client = TestClient(module_app)
    assert module_client.get("/api/v1/health").status_code == 200
    assert module_client.get("/api/v1/ready").status_code == 200
    assert module_client.get("/api/v1/system/info").status_code == 200
    assert module_client.get("/api/v1/system/metrics").status_code == 200

    middleware_app = FastAPI()

    @middleware_app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @middleware_app.get("/protected")
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    middleware_app.add_middleware(RequestIDMiddleware)
    middleware_app.add_middleware(LoggingMiddleware)
    middleware_app.add_middleware(AuthMiddleware, settings=Settings())
    middleware_client = TestClient(middleware_app)
    assert middleware_client.get("/health").status_code == 200
    unauthorized = middleware_client.get("/protected")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["message_key"] == "auth.unauthorized"

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

    payload = success_response(message="ok", message_key=build_message_key("jobs", "triggered"))
    assert payload["message_key"] == "jobs.triggered"
    assert error_response(
        ExternalServiceException(
            message="down",
            message_key="system.external_failure",
            error_code="SYSTEM_999",
        )
    )["error"]["code"] == "SYSTEM_999"

    validation_exc = ValidationException(message="bad", error_code="VAL_001")
    auth_exc = AuthenticationException()
    authz_exc = AuthorizationException()
    rate_limit_exc = RateLimitException()
    assert validation_exc.message_key == BaseMessageKeys.VALIDATION_ERROR
    assert auth_exc.status_code == 401
    assert authz_exc.status_code == 403
    assert rate_limit_exc.message_key == "auth.rate_limited"

    app_from_factory = create_app(Settings())
    assert app_from_factory.title == "pipeline-execution"

    class DummyModule:
        name = "health"

        def __init__(self) -> None:
            self.registered = False

        def register_routes(self) -> APIRouter:
            routes = APIRouter()

            @routes.get("/status")
            def status() -> dict[str, str]:
                return {"status": "ok"}

            return routes

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
        tasks = bootstrap_celery_tasks(celery_app=Celery("test"), settings=Settings(auto_discover_modules=False))
    finally:
        ModuleRegistry.load_modules = original_load_modules
    assert modules == [boot_module]
    assert tasks == []
    assert boot_module.registered is True

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
