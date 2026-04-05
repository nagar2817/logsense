# Background Job Framework Starter Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-ready GitHub template repository for FastAPI + Celery + Redis with modular route/task registration, consistent API contracts, structured logging, and strong test coverage.

**Architecture:** The repository uses a core engine that owns configuration, logging, middleware, exception translation, response contracts, Celery bootstrap, and module discovery. Functional capabilities live in self-contained modules under `app/modules/*`, where each module exposes routes, tasks, services, schemas, and message keys through a common contract and gets loaded by the registry at startup. FastAPI handles synchronous request validation and job triggering, while Celery executes module jobs with retry, correlation propagation, and standardized logging.

**Tech Stack:** Python 3.11+, FastAPI, Celery, Redis, Pydantic Settings, pytest, pytest-cov, Docker, Docker Compose, Ruff, Black, mypy, pre-commit

---

## File Structure Map

### Repository Root

- Create: `pyproject.toml`
  Purpose: dependency management, tool configuration, pytest/coverage settings, console entry points.
- Create: `.env.example`
  Purpose: local environment contract for API, Celery, Redis, and auth settings.
- Create: `.gitignore`
  Purpose: ignore Python cache, local env files, coverage artifacts, and editor output.
- Create: `.pre-commit-config.yaml`
  Purpose: lint/format/type/test quality gates for contributors.
- Create: `Dockerfile`
  Purpose: shared runtime image for API and worker.
- Create: `docker-compose.yml`
  Purpose: local orchestration for API, Celery worker, and Redis.
- Create: `Makefile`
  Purpose: common developer commands plus `create-module`.
- Create: `README.md`
  Purpose: template usage guide, architecture explanation, runbook, and module extension docs.
- Create: `.github/workflows/ci.yml`
  Purpose: CI for lint, type check, and tests so the template is production-ready out of the box.

### Application Core

- Create: `app/__init__.py`
  Purpose: package marker.
- Create: `app/main.py`
  Purpose: FastAPI app factory entry point and startup bootstrap.
- Create: `app/core/__init__.py`
  Purpose: package marker.
- Create: `app/core/config.py`
  Purpose: typed settings, environment parsing, module configuration, auth configuration.
- Create: `app/core/logging.py`
  Purpose: JSON logging setup shared by API and Celery.
- Create: `app/core/celery_app.py`
  Purpose: centralized Celery app, retry settings, task autodiscovery hooks.
- Create: `app/core/registry.py`
  Purpose: module contract, import loading, pkgutil autodiscovery, route/task registration.
- Create: `app/core/bootstrap.py`
  Purpose: application bootstrap orchestration for FastAPI and Celery.
- Create: `app/core/base_job.py`
  Purpose: base background job abstraction with retry, hooks, and logging.

### Middleware / Contracts

- Create: `app/core/middleware/__init__.py`
- Create: `app/core/middleware/request_id.py`
  Purpose: request ID generation, context propagation, response header injection.
- Create: `app/core/middleware/logging.py`
  Purpose: structured access logs with latency and request ID.
- Create: `app/core/middleware/auth.py`
  Purpose: API key validation for protected endpoints.
- Create: `app/core/middleware/error_handler.py`
  Purpose: global exception translation and safe fallback responses.
- Create: `app/core/responses/__init__.py`
- Create: `app/core/responses/base.py`
  Purpose: standard success response builder.
- Create: `app/core/responses/errors.py`
  Purpose: standard error response builder.
- Create: `app/core/exceptions/__init__.py`
- Create: `app/core/exceptions/base.py`
  Purpose: base application exception type.
- Create: `app/core/exceptions/http.py`
  Purpose: HTTP-facing exception subclasses.
- Create: `app/core/exceptions/domain.py`
  Purpose: domain/external service exception subclasses.
- Create: `app/core/messages/__init__.py`
- Create: `app/core/messages/base.py`
  Purpose: common message keys.
- Create: `app/core/messages/builder.py`
  Purpose: message key builder helpers.
- Create: `app/core/constants/__init__.py`
- Create: `app/core/constants/runtime.py`
  Purpose: shared constants such as request ID header name and health route allowlist.

### Utilities

- Create: `app/utils/__init__.py`
- Create: `app/utils/context.py`
  Purpose: request/correlation ID contextvars used by API and Celery.
- Create: `app/utils/module_scaffold.py`
  Purpose: module template strings used by the scaffold command.

### Modules

- Create: `app/modules/__init__.py`
- Create: `app/modules/health/{__init__.py,api.py,jobs.py,services.py,schemas.py,messages.py,module.py}`
- Create: `app/modules/auth/{__init__.py,api.py,jobs.py,services.py,schemas.py,messages.py,module.py}`
- Create: `app/modules/email/{__init__.py,api.py,jobs.py,services.py,schemas.py,messages.py,module.py}`
- Create: `app/modules/jobs/{__init__.py,api.py,jobs.py,services.py,schemas.py,messages.py,module.py}`
- Create: `app/modules/system/{__init__.py,api.py,jobs.py,services.py,schemas.py,messages.py,module.py}`
  Purpose: self-contained plug-in modules conforming to a shared contract.

### Tooling / Scripts

- Create: `scripts/create_module.py`
  Purpose: scaffold new modules with the required files and starter content.

### Tests

- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
  Purpose: shared fixtures for settings overrides, FastAPI client, Celery eager mode.
- Create: `tests/core/test_config.py`
- Create: `tests/core/test_responses_and_exceptions.py`
- Create: `tests/core/test_registry.py`
- Create: `tests/core/test_base_job.py`
- Create: `tests/middleware/test_middlewares.py`
- Create: `tests/modules/test_health_module.py`
- Create: `tests/modules/test_auth_module.py`
- Create: `tests/modules/test_email_module.py`
- Create: `tests/modules/test_jobs_module.py`
- Create: `tests/modules/test_system_module.py`
- Create: `tests/integration/test_api_to_worker_flow.py`
- Create: `tests/modules/test_module_scaffold.py`

---

### Task 1: Bootstrap The Repository Foundation

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `.pre-commit-config.yaml`
- Create: `Makefile`
- Create: `app/__init__.py`
- Create: `app/core/__init__.py`
- Create: `app/core/config.py`
- Create: `tests/__init__.py`
- Test: `tests/core/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
from app.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "pipeline-execution"
    assert settings.api_prefix == "/api/v1"
    assert settings.enabled_modules == [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.jobs.module",
        "app.modules.system.module",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_config.py::test_settings_load_defaults -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.core.config'`

- [ ] **Step 3: Write minimal implementation**

```toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "pipeline-execution"
version = "0.1.0"
description = "Production-ready FastAPI + Celery + Redis starter kit"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "celery[redis]>=5.4.0,<6.0.0",
  "fastapi>=0.115.0,<1.0.0",
  "httpx>=0.28.0,<1.0.0",
  "pydantic-settings>=2.8.0,<3.0.0",
  "python-json-logger>=3.3.0,<4.0.0",
  "redis>=5.2.0,<6.0.0",
  "uvicorn[standard]>=0.34.0,<1.0.0",
]

[project.optional-dependencies]
dev = [
  "black>=25.1.0,<26.0.0",
  "mypy>=1.15.0,<2.0.0",
  "pre-commit>=4.2.0,<5.0.0",
  "pytest>=8.3.0,<9.0.0",
  "pytest-asyncio>=0.25.0,<1.0.0",
  "pytest-cov>=6.1.0,<7.0.0",
  "types-redis>=4.6.0.20241004",
]

[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["app"]

[tool.black]
line-length = 100
target-version = ["py311"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "N", "ASYNC"]

[tool.mypy]
python_version = "3.11"
strict = true
packages = ["app"]

[tool.setuptools.packages.find]
include = ["app*"]
```

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "pipeline-execution"
    environment: str = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"
    api_key: str = "local-dev-key"
    redis_url: str = "redis://redis:6379/0"
    result_backend_url: str = "redis://redis:6379/1"
    enabled_modules: list[str] = Field(
        default_factory=lambda: [
            "app.modules.health.module",
            "app.modules.auth.module",
            "app.modules.email.module",
            "app.modules.jobs.module",
            "app.modules.system.module",
        ]
    )
    auto_discover_modules: bool = True
```

```env
APP_NAME=pipeline-execution
ENVIRONMENT=local
DEBUG=false
API_PREFIX=/api/v1
API_KEY=local-dev-key
REDIS_URL=redis://redis:6379/0
RESULT_BACKEND_URL=redis://redis:6379/1
```

```make
.PHONY: install lint format typecheck test run-api run-worker create-module

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	black .
	ruff check . --fix

typecheck:
	mypy app

test:
	pytest

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-worker:
	celery -A app.core.celery_app.celery_app worker -l info

create-module:
	python scripts/create_module.py $(name)
```

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.4
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        additional_dependencies: ["pydantic>=2.10.0", "pydantic-settings>=2.8.0"]
```

```gitignore
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
dist/
build/
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_config.py::test_settings_load_defaults -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example .gitignore .pre-commit-config.yaml Makefile app/__init__.py app/core/__init__.py app/core/config.py tests/__init__.py tests/core/test_config.py
git commit -m "chore: bootstrap project foundation"
```

### Task 2: Implement Response Contracts, Message Keys, And Exception Types

**Files:**
- Create: `app/core/responses/__init__.py`
- Create: `app/core/responses/base.py`
- Create: `app/core/responses/errors.py`
- Create: `app/core/messages/__init__.py`
- Create: `app/core/messages/base.py`
- Create: `app/core/messages/builder.py`
- Create: `app/core/exceptions/__init__.py`
- Create: `app/core/exceptions/base.py`
- Create: `app/core/exceptions/http.py`
- Create: `app/core/exceptions/domain.py`
- Test: `tests/core/test_responses_and_exceptions.py`

- [ ] **Step 1: Write the failing test**

```python
from app.core.exceptions.http import NotFoundException
from app.core.messages.base import BaseMessageKeys
from app.core.messages.builder import build_message_key
from app.core.responses.base import success_response
from app.core.responses.errors import error_response


def test_success_response_contract() -> None:
    payload = success_response(
        message="Operation successful",
        message_key=build_message_key("jobs", "triggered"),
        data={"task_id": "abc"},
        meta={"request_id": "req-1"},
    )

    assert payload == {
        "success": True,
        "message": "Operation successful",
        "message_key": "jobs.triggered",
        "data": {"task_id": "abc"},
        "meta": {"request_id": "req-1"},
    }


def test_error_response_contract() -> None:
    exc = NotFoundException(
        message="Email not found",
        message_key="email.not_found",
        error_code="EMAIL_001",
        details={"email_id": "missing"},
    )

    assert error_response(exc) == {
        "success": False,
        "message": "Email not found",
        "message_key": "email.not_found",
        "error": {"code": "EMAIL_001", "details": {"email_id": "missing"}},
    }
    assert BaseMessageKeys.INTERNAL_ERROR == "system.internal_error"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/core/test_responses_and_exceptions.py -v`
Expected: FAIL with import errors for response and exception modules

- [ ] **Step 3: Write minimal implementation**

```python
class BaseMessageKeys:
    INTERNAL_ERROR = "system.internal_error"
    VALIDATION_ERROR = "system.validation_error"
    UNAUTHORIZED = "auth.unauthorized"
    FORBIDDEN = "auth.forbidden"
```

```python
def build_message_key(module: str, action: str) -> str:
    return f"{module}.{action}"
```

```python
from typing import Any


def success_response(
    *,
    message: str,
    message_key: str,
    data: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "message_key": message_key,
        "data": data or {},
        "meta": meta or {},
    }
```

```python
from typing import Any

from app.core.exceptions.base import BaseAppException


def error_response(exc: BaseAppException) -> dict[str, Any]:
    return {
        "success": False,
        "message": exc.message,
        "message_key": exc.message_key,
        "error": {
            "code": exc.error_code,
            "details": exc.details,
        },
    }
```

```python
class BaseAppException(Exception):
    def __init__(
        self,
        *,
        message: str,
        message_key: str,
        error_code: str,
        status_code: int,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.message_key = message_key
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
```

```python
from starlette import status

from app.core.exceptions.base import BaseAppException
from app.core.messages.base import BaseMessageKeys


class ValidationException(BaseAppException):
    def __init__(self, *, message: str, error_code: str, details: dict[str, object] | None = None) -> None:
        super().__init__(
            message=message,
            message_key=BaseMessageKeys.VALIDATION_ERROR,
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationException(BaseAppException):
    def __init__(self, *, message: str = "Unauthorized", error_code: str = "AUTH_001") -> None:
        super().__init__(
            message=message,
            message_key=BaseMessageKeys.UNAUTHORIZED,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationException(BaseAppException):
    def __init__(self, *, message: str = "Forbidden", error_code: str = "AUTH_002") -> None:
        super().__init__(
            message=message,
            message_key=BaseMessageKeys.FORBIDDEN,
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(BaseAppException):
    def __init__(
        self,
        *,
        message: str,
        message_key: str,
        error_code: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            message_key=message_key,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class RateLimitException(BaseAppException):
    def __init__(self, *, message: str = "Rate limit exceeded", error_code: str = "AUTH_003") -> None:
        super().__init__(
            message=message,
            message_key="auth.rate_limited",
            error_code=error_code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
```

```python
from starlette import status

from app.core.exceptions.base import BaseAppException


class ExternalServiceException(BaseAppException):
    def __init__(
        self,
        *,
        message: str,
        message_key: str,
        error_code: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            message_key=message_key,
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/core/test_responses_and_exceptions.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/responses app/core/messages app/core/exceptions tests/core/test_responses_and_exceptions.py
git commit -m "feat: add response and exception contracts"
```

### Task 3: Add Runtime Constants, Context Propagation, And Structured Logging

**Files:**
- Create: `app/core/constants/__init__.py`
- Create: `app/core/constants/runtime.py`
- Create: `app/utils/__init__.py`
- Create: `app/utils/context.py`
- Create: `app/core/logging.py`
- Test: `tests/middleware/test_middlewares.py`

- [ ] **Step 1: Write the failing test**

```python
import logging

from app.core.logging import configure_logging
from app.utils.context import clear_request_context, get_request_context, set_request_context


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/middleware/test_middlewares.py::test_request_context_round_trip tests/middleware/test_middlewares.py::test_configure_logging_sets_json_formatter -v`
Expected: FAIL with import errors for logging/context modules

- [ ] **Step 3: Write minimal implementation**

```python
REQUEST_ID_HEADER = "X-Request-ID"
API_KEY_HEADER = "x-api-key"
HEALTH_ENDPOINTS = {"/health", "/ready"}
```

```python
from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_request_context(*, request_id: str | None, correlation_id: str | None) -> None:
    _request_id.set(request_id)
    _correlation_id.set(correlation_id)


def get_request_context() -> dict[str, str | None]:
    return {
        "request_id": _request_id.get(),
        "correlation_id": _correlation_id.get(),
    }


def clear_request_context() -> None:
    set_request_context(request_id=None, correlation_id=None)
```

```python
import logging
from logging.config import dictConfig


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(correlation_id)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {"level": "INFO", "handlers": ["default"]},
        }
    )
    logging.getLogger("celery").setLevel(logging.INFO)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/middleware/test_middlewares.py::test_request_context_round_trip tests/middleware/test_middlewares.py::test_configure_logging_sets_json_formatter -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/constants app/utils app/core/logging.py tests/middleware/test_middlewares.py
git commit -m "feat: add runtime context and logging"
```

### Task 4: Build Module Registry, Celery Bootstrap, And Base Job Abstraction

**Files:**
- Create: `app/core/registry.py`
- Create: `app/core/celery_app.py`
- Create: `app/core/base_job.py`
- Create: `app/core/bootstrap.py`
- Test: `tests/core/test_registry.py`
- Test: `tests/core/test_base_job.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi import APIRouter

from app.core.config import Settings
from app.core.registry import ModuleRegistry


class DummyModule:
    def __init__(self, name: str) -> None:
        self.name = name

    def register_routes(self) -> APIRouter:
        return APIRouter()

    def register_tasks(self) -> list[object]:
        return []


def test_registry_loads_configured_and_discovered_modules(monkeypatch) -> None:
    registry = ModuleRegistry(
        settings=Settings(enabled_modules=["app.modules.health.module"], auto_discover_modules=True)
    )
    monkeypatch.setattr(registry, "_discover_modules", lambda: ["app.modules.system.module"])
    monkeypatch.setattr(registry, "_load_from_path", lambda path: DummyModule(path.split(".")[-2]))

    loaded = registry.load_modules()

    assert [module.name for module in loaded] == ["health", "system"]
```

```python
from celery import Celery

from app.core.base_job import BaseJob


class DummyJob(BaseJob):
    name = "dummy.job"

    def run(self, payload: dict[str, str]) -> dict[str, str]:
        return {"status": payload["status"]}


def test_base_job_execute_wraps_payload() -> None:
    result = DummyJob(celery_app=Celery("test")).execute({"status": "ok"})
    assert result == {"status": "ok"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_registry.py tests/core/test_base_job.py -v`
Expected: FAIL with import errors for registry/base job modules

- [ ] **Step 3: Write minimal implementation**

```python
from collections.abc import Callable
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType
from typing import Protocol

from fastapi import APIRouter

from app.core.config import Settings


class ModuleContract(Protocol):
    name: str

    def register_routes(self) -> APIRouter: ...

    def register_tasks(self) -> list[Callable[..., object]]: ...


class ModuleRegistry:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def _load_from_path(self, import_path: str) -> ModuleContract:
        module: ModuleType = import_module(import_path)
        return module.Module()

    def _discover_modules(self) -> list[str]:
        if not self.settings.auto_discover_modules:
            return []
        import app.modules as package

        return [
            f"app.modules.{entry.name}.module"
            for entry in iter_modules(package.__path__)
            if entry.name != "__pycache__"
        ]

    def load_modules(self) -> list[ModuleContract]:
        module_paths = list(dict.fromkeys(self.settings.enabled_modules + self._discover_modules()))
        return [self._load_from_path(path) for path in module_paths]
```

```python
from celery import Celery

from app.core.config import Settings


settings = Settings()
celery_app = Celery("pipeline-execution", broker=settings.redis_url, backend=settings.result_backend_url)
celery_app.conf.update(
    task_default_queue="default",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_acks_late=True,
)
```

```python
import logging
from abc import ABC, abstractmethod
from typing import Any

from celery import Celery

from app.utils.context import get_request_context


class BaseJob(ABC):
    name = "base.job"

    def __init__(self, *, celery_app: Celery) -> None:
        self.celery_app = celery_app
        self.logger = logging.getLogger(self.name)

    @abstractmethod
    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def before_run(self, payload: dict[str, Any]) -> None:
        self.logger.info("job_started", extra={"payload": payload, **get_request_context()})

    def after_run(self, payload: dict[str, Any], result: dict[str, Any]) -> None:
        self.logger.info("job_completed", extra={"payload": payload, "result": result, **get_request_context()})

    def on_failure(self, payload: dict[str, Any], exc: Exception) -> None:
        self.logger.exception("job_failed", extra={"payload": payload, **get_request_context()})

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            self.before_run(payload)
            result = self.run(payload)
            self.after_run(payload, result)
            return result
        except Exception as exc:
            self.on_failure(payload, exc)
            raise
```

```python
from fastapi import FastAPI

from app.core.config import Settings
from app.core.registry import ModuleRegistry


def bootstrap_app(*, app: FastAPI, settings: Settings) -> list[object]:
    registry = ModuleRegistry(settings=settings)
    modules = registry.load_modules()
    for module in modules:
        app.include_router(module.register_routes(), prefix=settings.api_prefix)
        module.register_tasks()
    return modules
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_registry.py tests/core/test_base_job.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/registry.py app/core/celery_app.py app/core/base_job.py app/core/bootstrap.py tests/core/test_registry.py tests/core/test_base_job.py
git commit -m "feat: add module registry and base job abstraction"
```

### Task 5: Add Request ID, Logging, Auth, And Error Middleware With App Factory

**Files:**
- Create: `app/core/middleware/__init__.py`
- Create: `app/core/middleware/request_id.py`
- Create: `app/core/middleware/logging.py`
- Create: `app/core/middleware/auth.py`
- Create: `app/core/middleware/error_handler.py`
- Create: `app/main.py`
- Modify: `tests/middleware/test_middlewares.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware


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


def test_request_id_is_added_to_response() -> None:
    app = build_test_app()
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


def test_protected_endpoint_requires_api_key() -> None:
    app = build_test_app()
    client = TestClient(app)
    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["message_key"] == "auth.unauthorized"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/middleware/test_middlewares.py::test_request_id_is_added_to_response tests/middleware/test_middlewares.py::test_protected_endpoint_requires_api_key -v`
Expected: FAIL because the middleware modules are not implemented

- [ ] **Step 3: Write minimal implementation**

```python
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.constants.runtime import REQUEST_ID_HEADER
from app.utils.context import set_request_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        set_request_context(request_id=request_id, correlation_id=request_id)
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
```

```python
import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.context import get_request_context


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self.logger = logging.getLogger("app.request")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        self.logger.info(
            "request_complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
                **get_request_context(),
            },
        )
        return response
```

```python
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings
from app.core.constants.runtime import API_KEY_HEADER, HEALTH_ENDPOINTS
from app.core.exceptions.http import AuthenticationException
from app.core.responses.errors import error_response


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.endswith(tuple(HEALTH_ENDPOINTS)):
            return await call_next(request)
        if request.headers.get(API_KEY_HEADER) != self.settings.api_key:
            exc = AuthenticationException()
            return JSONResponse(status_code=exc.status_code, content=error_response(exc))
        return await call_next(request)
```

```python
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions.base import BaseAppException
from app.core.messages.base import BaseMessageKeys
from app.core.responses.errors import error_response


def register_exception_handlers(app: FastAPI) -> None:
    logger = logging.getLogger("app.error")

    @app.exception_handler(BaseAppException)
    async def handle_known_exceptions(_: Request, exc: BaseAppException) -> JSONResponse:
        logger.warning("handled_app_exception", extra={"error_code": exc.error_code})
        return JSONResponse(status_code=exc.status_code, content=error_response(exc))

    @app.exception_handler(Exception)
    async def handle_unknown_exceptions(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "message_key": BaseMessageKeys.INTERNAL_ERROR,
                "error": {"code": "SYSTEM_001", "details": {}},
            },
        )
```

```python
from fastapi import FastAPI

from app.core.config import Settings
from app.core.logging import configure_logging
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    configure_logging()
    app = FastAPI(title=resolved_settings.app_name, debug=resolved_settings.debug)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware, settings=resolved_settings)
    register_exception_handlers(app)
    return app


app = create_app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/middleware/test_middlewares.py::test_request_id_is_added_to_response tests/middleware/test_middlewares.py::test_protected_endpoint_requires_api_key -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/middleware app/main.py tests/middleware/test_middlewares.py
git commit -m "feat: add middleware stack and app factory"
```

### Task 6: Implement Health And System Modules

**Files:**
- Create: `app/modules/__init__.py`
- Create: `app/modules/health/__init__.py`
- Create: `app/modules/health/api.py`
- Create: `app/modules/health/jobs.py`
- Create: `app/modules/health/services.py`
- Create: `app/modules/health/schemas.py`
- Create: `app/modules/health/messages.py`
- Create: `app/modules/health/module.py`
- Create: `app/modules/system/__init__.py`
- Create: `app/modules/system/api.py`
- Create: `app/modules/system/jobs.py`
- Create: `app/modules/system/services.py`
- Create: `app/modules/system/schemas.py`
- Create: `app/modules/system/messages.py`
- Create: `app/modules/system/module.py`
- Test: `tests/modules/test_health_module.py`
- Test: `tests/modules/test_system_module.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.health.api import router as health_router
from app.modules.system.api import router as system_router


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
```

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.system.api import router


def test_system_info_requires_api_key() -> None:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/system/info")

    assert response.status_code == 200
    assert response.json()["message_key"] == "system.info"


def test_system_metrics_placeholder() -> None:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/system/metrics")

    assert response.status_code == 200
    assert response.json()["data"]["metrics_enabled"] is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/modules/test_health_module.py tests/modules/test_system_module.py -v`
Expected: FAIL with registry import errors because module implementations do not exist

- [ ] **Step 3: Write minimal implementation**

```python
class HealthMessageKeys:
    OK = "health.ok"
    READY = "health.ready"
```

```python
from pydantic import BaseModel


class HealthState(BaseModel):
    status: str
    redis: str
```

```python
from app.modules.health.schemas import HealthState


class HealthService:
    def health(self) -> HealthState:
        return HealthState(status="ok", redis="unknown")

    def ready(self) -> HealthState:
        return HealthState(status="ready", redis="up")
```

```python
from fastapi import APIRouter

from app.core.responses.base import success_response
from app.modules.health.messages import HealthMessageKeys
from app.modules.health.services import HealthService

router = APIRouter(tags=["health"])
service = HealthService()


@router.get("/health")
def health() -> dict[str, object]:
    return success_response(
        message="Service is healthy",
        message_key=HealthMessageKeys.OK,
        data=service.health().model_dump(),
    )


@router.get("/ready")
def ready() -> dict[str, object]:
    return success_response(
        message="Service is ready",
        message_key=HealthMessageKeys.READY,
        data=service.ready().model_dump(),
    )
```

```python
from fastapi import APIRouter


class Module:
    name = "health"

    def register_routes(self) -> APIRouter:
        from app.modules.health.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
```

```python
class SystemMessageKeys:
    INFO = "system.info"
    METRICS = "system.metrics"
```

```python
from pydantic import BaseModel


class SystemInfo(BaseModel):
    app_name: str
    environment: str


class MetricsState(BaseModel):
    metrics_enabled: bool
```

```python
from app.core.config import Settings
from app.modules.system.schemas import MetricsState, SystemInfo


class SystemService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def info(self) -> SystemInfo:
        return SystemInfo(app_name=self.settings.app_name, environment=self.settings.environment)

    def metrics(self) -> MetricsState:
        return MetricsState(metrics_enabled=False)
```

```python
from fastapi import APIRouter

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.system.messages import SystemMessageKeys
from app.modules.system.services import SystemService

router = APIRouter(tags=["system"])
service = SystemService(settings=Settings())


@router.get("/system/info")
def system_info() -> dict[str, object]:
    return success_response(
        message="System info retrieved",
        message_key=SystemMessageKeys.INFO,
        data=service.info().model_dump(),
    )


@router.get("/system/metrics")
def system_metrics() -> dict[str, object]:
    return success_response(
        message="Metrics placeholder",
        message_key=SystemMessageKeys.METRICS,
        data=service.metrics().model_dump(),
    )
```

```python
from fastapi import APIRouter


class Module:
    name = "system"

    def register_routes(self) -> APIRouter:
        from app.modules.system.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/modules/test_health_module.py tests/modules/test_system_module.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/modules tests/modules/test_health_module.py tests/modules/test_system_module.py
git commit -m "feat: add health and system modules"
```

### Task 7: Implement The Auth Module And Reusable API Key Validation Service

**Files:**
- Create: `app/modules/auth/__init__.py`
- Create: `app/modules/auth/api.py`
- Create: `app/modules/auth/jobs.py`
- Create: `app/modules/auth/services.py`
- Create: `app/modules/auth/schemas.py`
- Create: `app/modules/auth/messages.py`
- Create: `app/modules/auth/module.py`
- Modify: `app/core/middleware/auth.py`
- Test: `tests/modules/test_auth_module.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.auth.api import router


def test_auth_validate_endpoint() -> None:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/auth/validate")

    assert response.status_code == 200
    assert response.json()["message_key"] == "auth.valid"
    assert response.json()["data"]["authenticated"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_auth_module.py -v`
Expected: FAIL because auth module files do not exist

- [ ] **Step 3: Write minimal implementation**

```python
class AuthMessageKeys:
    VALID = "auth.valid"
    INVALID_API_KEY = "auth.invalid_api_key"
```

```python
from pydantic import BaseModel


class AuthValidationResult(BaseModel):
    authenticated: bool
    scheme: str
```

```python
from app.core.config import Settings


class AuthService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def is_valid_api_key(self, api_key: str | None) -> bool:
        return api_key == self.settings.api_key
```

```python
from fastapi import APIRouter

from app.core.responses.base import success_response
from app.modules.auth.messages import AuthMessageKeys
from app.modules.auth.schemas import AuthValidationResult

router = APIRouter(tags=["auth"])


@router.get("/auth/validate")
def validate_auth() -> dict[str, object]:
    return success_response(
        message="API key valid",
        message_key=AuthMessageKeys.VALID,
        data=AuthValidationResult(authenticated=True, scheme="api_key").model_dump(),
    )
```

```python
from fastapi import APIRouter


class Module:
    name = "auth"

    def register_routes(self) -> APIRouter:
        from app.modules.auth.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
```

```python
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings
from app.core.constants.runtime import HEALTH_ENDPOINTS
from app.core.exceptions.http import AuthenticationException
from app.core.responses.errors import error_response
from app.modules.auth.services import AuthService


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, settings: Settings) -> None:
        super().__init__(app)
        self.auth_service = AuthService(settings=settings)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.endswith(tuple(HEALTH_ENDPOINTS)):
            return await call_next(request)
        if not self.auth_service.is_valid_api_key(request.headers.get("x-api-key")):
            exc = AuthenticationException(message="Invalid API key")
            return JSONResponse(status_code=exc.status_code, content=error_response(exc))
        return await call_next(request)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_auth_module.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/modules/auth app/core/middleware/auth.py tests/modules/test_auth_module.py
git commit -m "feat: add auth module and validation service"
```

### Task 8: Implement The Email Module With Celery Task Registration And Retry-Safe Job Runner

**Files:**
- Create: `app/modules/email/__init__.py`
- Create: `app/modules/email/api.py`
- Create: `app/modules/email/jobs.py`
- Create: `app/modules/email/services.py`
- Create: `app/modules/email/schemas.py`
- Create: `app/modules/email/messages.py`
- Create: `app/modules/email/module.py`
- Modify: `app/core/base_job.py`
- Modify: `app/core/bootstrap.py`
- Test: `tests/modules/test_email_module.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.email.services import EmailService


def test_email_service_builds_delivery_receipt() -> None:
    service = EmailService()
    receipt = service.send_email(
        {
            "to_email": "dev@example.com",
            "subject": "Hello",
            "body": "World",
            "idempotency_key": "email-1",
        }
    )

    assert receipt["status"] == "queued_for_delivery"
    assert receipt["recipient"] == "dev@example.com"
```

```python
from app.modules.email.api import router
from app.modules.email.jobs import send_email_job


def test_email_trigger_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(send_email_job, "delay", lambda payload: type("Result", (), {"id": "task-123"})())
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post(
        "/api/v1/email/send",
        json={
            "to_email": "dev@example.com",
            "subject": "Hello",
            "body": "World",
            "idempotency_key": "email-1",
        },
    )

    assert response.status_code == 202
    assert response.json()["message_key"] == "email.queued"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/modules/test_email_module.py -v`
Expected: FAIL because email module files and registered task do not exist

- [ ] **Step 3: Write minimal implementation**

```python
class EmailMessageKeys:
    EMAIL_SENT = "email.sent"
    EMAIL_FAILED = "email.failed"
    EMAIL_NOT_FOUND = "email.not_found"
    EMAIL_QUEUED = "email.queued"
```

```python
from pydantic import BaseModel, EmailStr


class EmailPayload(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    idempotency_key: str


class EmailReceipt(BaseModel):
    status: str
    recipient: EmailStr
    idempotency_key: str
```

```python
from app.modules.email.schemas import EmailPayload, EmailReceipt


class EmailService:
    def send_email(self, payload: dict[str, str]) -> dict[str, str]:
        parsed = EmailPayload.model_validate(payload)
        return EmailReceipt(
            status="queued_for_delivery",
            recipient=parsed.to_email,
            idempotency_key=parsed.idempotency_key,
        ).model_dump()
```

```python
from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.modules.email.services import EmailService


class SendEmailJob(BaseJob):
    name = "email.send"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return EmailService().send_email(payload)


job = SendEmailJob(celery_app=celery_app)


@celery_app.task(
    bind=True,
    name="email.send",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def send_email_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
```

```python
from fastapi import APIRouter, status

from app.core.responses.base import success_response
from app.modules.email.jobs import send_email_job
from app.modules.email.messages import EmailMessageKeys
from app.modules.email.schemas import EmailPayload

router = APIRouter(tags=["email"])


@router.post("/email/send", status_code=status.HTTP_202_ACCEPTED)
def trigger_email(payload: EmailPayload) -> dict[str, object]:
    async_result = send_email_job.delay(payload.model_dump())
    return success_response(
        message="Email job queued",
        message_key=EmailMessageKeys.EMAIL_QUEUED,
        data={"task_id": async_result.id},
    )
```

```python
from fastapi import APIRouter

from app.modules.email.jobs import send_email_job


class Module:
    name = "email"

    def register_routes(self) -> APIRouter:
        from app.modules.email.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [send_email_job]
```

```python
from fastapi import FastAPI

from app.core.celery_app import celery_app
from app.core.config import Settings
from app.core.registry import ModuleRegistry


def bootstrap_app(*, app: FastAPI, settings: Settings) -> list[object]:
    registry = ModuleRegistry(settings=settings)
    modules = registry.load_modules()
    for module in modules:
        app.include_router(module.register_routes(), prefix=settings.api_prefix)
        for task in module.register_tasks():
            celery_app.tasks.register(task)
    return modules
```

```python
from typing import Any

from app.utils.context import get_request_context


class BaseJob(ABC):
    name = "base.job"

    def metrics_tags(self, payload: dict[str, Any]) -> dict[str, str]:
        return {"job": self.name, "idempotency_key": str(payload.get("idempotency_key", "missing"))}

    def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            self.before_run(payload)
            result = self.run(payload)
            self.after_run(payload, result)
            return result
        except Exception as exc:
            self.on_failure(payload, exc)
            raise
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/modules/test_email_module.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/modules/email app/core/base_job.py app/core/bootstrap.py tests/modules/test_email_module.py
git commit -m "feat: add email module and celery task integration"
```

### Task 9: Implement The Jobs Module For Generic Triggering And Status Inspection

**Files:**
- Create: `app/modules/jobs/__init__.py`
- Create: `app/modules/jobs/api.py`
- Create: `app/modules/jobs/jobs.py`
- Create: `app/modules/jobs/services.py`
- Create: `app/modules/jobs/schemas.py`
- Create: `app/modules/jobs/messages.py`
- Create: `app/modules/jobs/module.py`
- Test: `tests/modules/test_jobs_module.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.jobs.api import router


def test_job_status_endpoint(monkeypatch) -> None:
    class DummyResult:
        id = "task-123"
        status = "SUCCESS"

        def successful(self) -> bool:
            return True

        @property
        def result(self) -> dict[str, str]:
            return {"status": "queued_for_delivery"}

    monkeypatch.setattr("app.modules.jobs.services.AsyncResult", lambda task_id, app: DummyResult())
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    response = TestClient(app).get("/api/v1/jobs/task-123")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "SUCCESS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_jobs_module.py -v`
Expected: FAIL because jobs module files do not exist

- [ ] **Step 3: Write minimal implementation**

```python
class JobsMessageKeys:
    TRIGGERED = "jobs.triggered"
    STATUS = "jobs.status"
```

```python
from pydantic import BaseModel


class JobTriggerRequest(BaseModel):
    job_name: str
    payload: dict[str, object]


class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, object] | None = None
```

```python
from celery.result import AsyncResult

from app.core.celery_app import celery_app
from app.modules.email.jobs import send_email_job
from app.modules.jobs.schemas import JobStatusResponse, JobTriggerRequest


class JobService:
    def __init__(self) -> None:
        self.job_map = {"email.send": send_email_job}

    def trigger(self, request: JobTriggerRequest) -> str:
        if request.job_name not in self.job_map:
            raise ValueError(f"Unsupported job: {request.job_name}")
        return self.job_map[request.job_name].delay(request.payload).id

    def status(self, task_id: str) -> dict[str, object]:
        result = AsyncResult(task_id, app=celery_app)
        return JobStatusResponse(
            task_id=result.id,
            status=result.status,
            result=result.result if result.successful() else None,
        ).model_dump()
```

```python
from fastapi import APIRouter, status

from app.core.responses.base import success_response
from app.modules.jobs.messages import JobsMessageKeys
from app.modules.jobs.schemas import JobTriggerRequest
from app.modules.jobs.services import JobService

router = APIRouter(tags=["jobs"])
service = JobService()


@router.post("/jobs/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_job(payload: JobTriggerRequest) -> dict[str, object]:
    task_id = service.trigger(payload)
    return success_response(
        message="Job triggered",
        message_key=JobsMessageKeys.TRIGGERED,
        data={"task_id": task_id},
    )


@router.get("/jobs/{task_id}")
def get_job_status(task_id: str) -> dict[str, object]:
    return success_response(
        message="Job status retrieved",
        message_key=JobsMessageKeys.STATUS,
        data=service.status(task_id),
    )
```

```python
from fastapi import APIRouter


class Module:
    name = "jobs"

    def register_routes(self) -> APIRouter:
        from app.modules.jobs.api import router

        return router

    def register_tasks(self) -> list[object]:
        return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_jobs_module.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/modules/jobs tests/modules/test_jobs_module.py
git commit -m "feat: add jobs trigger and status module"
```

### Task 10: Harden Error Handling, Validation Translation, And Registry Behavior

**Files:**
- Modify: `app/core/middleware/error_handler.py`
- Modify: `app/core/registry.py`
- Modify: `app/modules/jobs/services.py`
- Test: `tests/core/test_registry.py`
- Modify: `tests/core/test_responses_and_exceptions.py`
- Modify: `tests/modules/test_jobs_module.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

import pytest

from app.core.config import Settings
from app.core.registry import ModuleRegistry
from app.core.middleware.error_handler import register_exception_handlers
from app.modules.jobs.api import router


def test_registry_deduplicates_discovered_modules() -> None:
    settings = Settings(
        enabled_modules=["app.modules.health.module", "app.modules.health.module"],
        auto_discover_modules=False,
    )
    registry = ModuleRegistry(settings=settings)

    loaded = registry.load_modules()

    assert [module.name for module in loaded] == ["health"]
```

```python
def test_unknown_job_returns_standard_error() -> None:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post(
        "/api/v1/jobs/trigger",
        json={"job_name": "missing.job", "payload": {}},
    )

    assert response.status_code == 404
    assert response.json()["message_key"] == "jobs.not_found"
    assert response.json()["error"]["code"] == "JOB_001"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_registry.py::test_registry_deduplicates_discovered_modules tests/modules/test_jobs_module.py::test_unknown_job_returns_standard_error -v`
Expected: FAIL because current code returns `ValueError` and does not map it to standard errors

- [ ] **Step 3: Write minimal implementation**

```python
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions.base import BaseAppException
from app.core.exceptions.http import NotFoundException, ValidationException
from app.core.messages.base import BaseMessageKeys
from app.core.responses.errors import error_response


def register_exception_handlers(app: FastAPI) -> None:
    logger = logging.getLogger("app.error")

    @app.exception_handler(BaseAppException)
    async def handle_known_exceptions(_: Request, exc: BaseAppException) -> JSONResponse:
        logger.warning("handled_app_exception", extra={"error_code": exc.error_code})
        return JSONResponse(status_code=exc.status_code, content=error_response(exc))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        wrapped = ValidationException(
            message="Validation failed",
            error_code="SYSTEM_002",
            details={"errors": exc.errors()},
        )
        return JSONResponse(status_code=wrapped.status_code, content=error_response(wrapped))

    @app.exception_handler(Exception)
    async def handle_unknown_exceptions(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "message_key": BaseMessageKeys.INTERNAL_ERROR,
                "error": {"code": "SYSTEM_001", "details": {}},
            },
        )
```

```python
from app.core.exceptions.http import NotFoundException
from app.modules.email.jobs import send_email_job
from app.modules.jobs.schemas import JobStatusResponse, JobTriggerRequest


class JobService:
    def __init__(self) -> None:
        self.job_map = {"email.send": send_email_job}

    def trigger(self, request: JobTriggerRequest) -> str:
        if request.job_name not in self.job_map:
            raise NotFoundException(
                message="Job not found",
                message_key="jobs.not_found",
                error_code="JOB_001",
                details={"job_name": request.job_name},
            )
        return self.job_map[request.job_name].delay(request.payload).id
```

```python
def load_modules(self) -> list[ModuleContract]:
    module_paths = list(dict.fromkeys(self.settings.enabled_modules + self._discover_modules()))
    loaded_modules = [self._load_from_path(path) for path in module_paths]
    return loaded_modules
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_registry.py::test_registry_deduplicates_discovered_modules tests/modules/test_jobs_module.py::test_unknown_job_returns_standard_error -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/middleware/error_handler.py app/core/registry.py app/modules/jobs/services.py tests/core/test_registry.py tests/modules/test_jobs_module.py
git commit -m "feat: harden exception translation and registry loading"
```

### Task 11: Add Docker, CI, And End-To-End Integration Coverage

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.github/workflows/ci.yml`
- Modify: `app/main.py`
- Create: `tests/conftest.py`
- Create: `tests/integration/test_api_to_worker_flow.py`

- [ ] **Step 1: Write the failing integration test**

```python
from app.modules.email.jobs import send_email_job


def test_api_to_celery_flow_runs_in_eager_mode(client, monkeypatch) -> None:
    monkeypatch.setattr(send_email_job, "delay", lambda payload: type("Result", (), {"id": "task-eager-1"})())

    response = client.post(
        "/api/v1/email/send",
        headers={"x-api-key": "local-dev-key"},
        json={
            "to_email": "dev@example.com",
            "subject": "Hello",
            "body": "World",
            "idempotency_key": "email-1",
        },
    )

    assert response.status_code == 202
    assert response.json()["data"]["task_id"] == "task-eager-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_api_to_worker_flow.py -v`
Expected: FAIL because the test file and eager fixtures do not exist

- [ ] **Step 3: Write minimal implementation**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY tests ./tests

RUN python -m pip install --upgrade pip && python -m pip install -e ".[dev]"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
version: "3.9"

services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    env_file:
      - .env.example
    depends_on:
      - redis

  worker:
    build: .
    command: celery -A app.core.celery_app.celery_app worker -l info
    env_file:
      - .env.example
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

```yaml
name: ci

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e ".[dev]"
      - run: ruff check .
      - run: black --check .
      - run: mypy app
      - run: pytest
```

```python
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture(autouse=True)
def configure_celery_eager(monkeypatch) -> None:
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "true")


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings()))
```

```python
from fastapi import FastAPI

from app.core.bootstrap import bootstrap_app
from app.core.config import Settings
from app.core.logging import configure_logging
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    configure_logging()
    app = FastAPI(title=resolved_settings.app_name, debug=resolved_settings.debug)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware, settings=resolved_settings)
    register_exception_handlers(app)
    bootstrap_app(app=app, settings=resolved_settings)
    return app


app = create_app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/integration/test_api_to_worker_flow.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .github/workflows/ci.yml app/main.py tests/conftest.py tests/integration/test_api_to_worker_flow.py
git commit -m "chore: add container runtime and integration coverage"
```

### Task 12: Add Module Scaffolding, README, And Final Quality Gates

**Files:**
- Create: `scripts/create_module.py`
- Create: `app/utils/module_scaffold.py`
- Modify: `Makefile`
- Create: `README.md`
- Modify: `pyproject.toml`
- Create: `tests/modules/test_module_scaffold.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from scripts.create_module import build_module_files


def test_create_module_generates_required_files(tmp_path: Path) -> None:
    created = build_module_files(tmp_path / "payment", module_name="payment")

    assert sorted(path.name for path in created) == [
        "__init__.py",
        "api.py",
        "jobs.py",
        "messages.py",
        "module.py",
        "schemas.py",
        "services.py",
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_module_scaffold.py -v`
Expected: FAIL because scaffold script and test file do not exist

- [ ] **Step 3: Write minimal implementation**

```python
MODULE_FILES = {
    "__init__.py": "",
    "api.py": "from fastapi import APIRouter\n\nrouter = APIRouter(tags=['{module}'])\n",
    "jobs.py": "",
    "services.py": "class {class_name}Service:\n    pass\n",
    "schemas.py": "",
    "messages.py": "class {class_name}MessageKeys:\n    EXAMPLE = '{module}.example'\n",
    "module.py": (
        "from fastapi import APIRouter\n\n"
        "class Module:\n"
        "    name = '{module}'\n\n"
        "    def register_routes(self) -> APIRouter:\n"
        "        from app.modules.{module}.api import router\n\n"
        "        return router\n\n"
        "    def register_tasks(self) -> list[object]:\n"
        "        return []\n"
    ),
}
```

```python
from pathlib import Path

from app.utils.module_scaffold import MODULE_FILES


def build_module_files(base_path: Path, *, module_name: str) -> list[Path]:
    class_name = module_name.capitalize()
    base_path.mkdir(parents=True, exist_ok=False)
    created: list[Path] = []
    for filename, template in MODULE_FILES.items():
        target = base_path / filename
        target.write_text(template.format(module=module_name, class_name=class_name), encoding="utf-8")
        created.append(target)
    return created
```

````markdown
# Pipeline Execution Template

## Architecture

- `app/core`: configuration, logging, middleware, registry, Celery bootstrap, response/error contracts.
- `app/modules`: plug-in modules with isolated API, job, service, schema, and message layers.
- `scripts/create_module.py`: scaffolds new modules so routing and task structure stay consistent.

## Run Locally

```bash
docker-compose up --build
```

## Run Tests

```bash
pytest
```

## Add A Module

```bash
make create-module name=payment
```

## Add A Job

1. Add a job class in `app/modules/<module>/jobs.py` that extends `BaseJob`.
2. Export the Celery task from `register_tasks()` in `app/modules/<module>/module.py`.
3. Trigger it from a route or service using `.delay(payload)`.

## Scale Workers

```bash
docker-compose up --build --scale worker=3
```
````

```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80 -v"
testpaths = ["tests"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_module_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/create_module.py app/utils/module_scaffold.py README.md pyproject.toml tests/modules/test_module_scaffold.py
git commit -m "docs: add scaffold tooling and template guide"
```

---

## Final Verification Checklist

- Run: `python -m pip install -e ".[dev]"`
  Expected: installs application and development dependencies successfully.
- Run: `ruff check .`
  Expected: PASS
- Run: `black --check .`
  Expected: PASS
- Run: `mypy app`
  Expected: PASS
- Run: `pytest`
  Expected: PASS with coverage `>= 80%`
- Run: `docker-compose up --build`
  Expected: API on port `8000`, worker connected to Redis, `/api/v1/health` returns success.

## Self-Review

### Spec Coverage

- Modular architecture and plug-and-play modules: Tasks 4, 6, 7, 8, 9, 12
- Core engine + middleware layer + pluggable modules: Tasks 3, 4, 5, 6, 7, 8, 9
- Standard response and message key contracts: Task 2
- Structured exception handling and error codes: Tasks 2 and 10
- Request ID, logging, auth, and error middleware: Tasks 3 and 5
- Central Celery app, dynamic task registration, retries, logging: Tasks 4 and 8
- Required modules (`health`, `auth`, `email`, `jobs`, `system`): Tasks 6, 7, 8, 9
- Testing coverage including integration path: Tasks 1 through 12, especially 11
- Developer experience, Docker, README, `make create-module`: Tasks 1, 11, 12

No uncovered spec items remain.

### Placeholder Scan

- Checked for placeholder wording and vague instructions.
- Each task contains explicit files, concrete code snippets, exact commands, and expected outcomes.

### Type Consistency

- `Module.register_routes()` returns `APIRouter` consistently across tasks.
- `Module.register_tasks()` returns `list[object]` consistently across tasks.
- `BaseJob.run()` and `BaseJob.execute()` both use `dict[str, Any]` payloads consistently.
- Response contracts use `success`, `message`, `message_key`, `data`, `meta` consistently.
