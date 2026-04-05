import logging
import sys
from types import ModuleType, SimpleNamespace

from celery import Celery
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from app.core.base_job import BaseJob
from app.core.bootstrap import bootstrap_app
from app.core.config import Settings
from app.core.exceptions.domain import ExternalServiceException
from app.core.exceptions.http import (
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.main import create_app
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware
from app.core.messages.base import BaseMessageKeys
from app.core.messages.builder import build_message_key
from app.core.logging import configure_logging
from app.core.registry import ModuleRegistry
from app.core.responses.base import success_response
from app.core.responses.errors import error_response
from app.utils.context import clear_request_context, get_request_context, set_request_context


def build_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/protected")
    def protected() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware, settings=Settings())
    return app


def test_request_context_round_trip() -> None:
    set_request_context(request_id="req-123", correlation_id="corr-123")

    assert get_request_context() == {
        "request_id": "req-123",
        "correlation_id": "corr-123",
    }

    clear_request_context()
    assert get_request_context() == {"request_id": None, "correlation_id": None}


def test_configure_logging_sets_json_formatter() -> None:
    configure_logging()
    root_handler = logging.getLogger().handlers[0]
    assert root_handler.formatter is not None


def test_request_id_is_added_to_response() -> None:
    app = build_test_app()
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers

    clear_request_context()
    assert get_request_context() == {"request_id": None, "correlation_id": None}
    configure_logging()
    assert logging.getLogger().handlers[0].formatter is not None

    payload = success_response(message="ok", message_key=build_message_key("jobs", "triggered"))
    assert payload["message_key"] == "jobs.triggered"
    assert payload["data"] == {}

    validation_exc = ValidationException(message="bad", error_code="VAL_001")
    authz_exc = AuthorizationException()
    rate_limit_exc = RateLimitException()
    external_exc = ExternalServiceException(
        message="down",
        message_key="system.external_failure",
        error_code="SYSTEM_999",
    )
    assert validation_exc.message_key == BaseMessageKeys.VALIDATION_ERROR
    assert authz_exc.message_key == BaseMessageKeys.FORBIDDEN
    assert rate_limit_exc.message_key == "auth.rate_limited"
    assert error_response(external_exc)["error"]["code"] == "SYSTEM_999"

    app_with_handlers = FastAPI()
    register_exception_handlers(app_with_handlers)

    @app_with_handlers.get("/not-found")
    def not_found() -> None:
        raise NotFoundException(
            message="Missing",
            message_key="email.not_found",
            error_code="EMAIL_001",
        )

    @app_with_handlers.get("/boom")
    def boom() -> None:
        raise RuntimeError("boom")

    handler_client = TestClient(app_with_handlers, raise_server_exceptions=False)
    not_found_response = handler_client.get("/not-found")
    boom_response = handler_client.get("/boom")
    assert not_found_response.status_code == 404
    assert boom_response.status_code == 500

    created_app = create_app(Settings())
    assert created_app.title == "pipeline-execution"


def test_protected_endpoint_requires_api_key() -> None:
    app = build_test_app()
    client = TestClient(app)
    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["message_key"] == "auth.unauthorized"

    auth_exc = AuthenticationException()
    assert auth_exc.status_code == 401

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

    class DummyJob(BaseJob):
        name = "dummy.job"

        def run(self, payload: dict[str, str]) -> dict[str, str]:
            return {"status": payload["status"]}

    class ModuleFromImport(DummyModule):
        pass

    module = DummyModule()
    boot_app = FastAPI()
    original_load_modules = ModuleRegistry.load_modules
    ModuleRegistry.load_modules = lambda self: [module]
    try:
        modules = bootstrap_app(app=boot_app, settings=Settings(auto_discover_modules=False))
    finally:
        ModuleRegistry.load_modules = original_load_modules
    assert modules == [module]
    assert module.registered is True
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
        imported_module = registry._load_from_path("app.modules.health.module")
        assert imported_module.name == "health"

        discovery_registry = ModuleRegistry(settings=Settings(auto_discover_modules=True))
        assert discovery_registry._discover_modules() == ["app.modules.health.module"]
    finally:
        registry_module.import_module = original_import_module
        registry_module.iter_modules = original_iter_modules
        if original_modules_package is None:
            sys.modules.pop("app.modules", None)
        else:
            sys.modules["app.modules"] = original_modules_package

    assert DummyJob(celery_app=Celery("test")).execute({"status": "ok"}) == {"status": "ok"}
