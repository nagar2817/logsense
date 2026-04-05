# LogSense AI Log Analysis MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the backend-only LogSense MVP that ingests logs, detects anomalous clusters, runs AI-assisted analysis, creates incidents and actions, and exposes dashboard APIs for logs, incidents, and actions.

**Architecture:** Keep the existing FastAPI + Celery modular starter, but add six product modules: `logs`, `analysis`, `ai`, `incident`, `actions`, and `alerts`. Persist MVP state in SQLite so the API process and Celery worker share durable storage without adding another service, use Celery for asynchronous pipeline stages after ingestion, and keep all module boundaries explicit so future Redis/Postgres or external alert integrations can replace the MVP persistence and placeholder interfaces cleanly.

**Tech Stack:** Python 3.11, FastAPI, Celery, Redis, SQLite3, Pydantic, httpx, pytest, pytest-cov

---

## Scope Check

This PRD spans multiple modules, but they are not independent subsystems. The ingestion, clustering, anomaly detection, AI analysis, incident creation, and action storage all depend on one shared pipeline and one shared persistence model. Keep this as a single execution plan.

## File Structure Map

### Core Wiring

- Modify: `app/core/config.py`
  Purpose: add LogSense runtime settings, remove the broken default `app.modules.jobs.module`, and register the new product modules.
- Modify: `app/core/bootstrap.py`
  Purpose: separate HTTP router bootstrap from Celery task bootstrap so both the API process and worker load modules correctly.
- Modify: `app/core/celery_app.py`
  Purpose: initialize the database and register module tasks when the worker imports the Celery app.
- Modify: `app/main.py`
  Purpose: initialize the database and load module routers during application startup.
- Create: `app/core/database.py`
  Purpose: SQLite connection helpers plus schema initialization for `logs`, `incidents`, and `actions`.
- Modify: `.env.example`
  Purpose: document the new database, anomaly-threshold, and LLM configuration contract.
- Modify: `tests/conftest.py`
  Purpose: isolate the added environment variables across tests.
- Modify: `tests/core/test_config.py`
  Purpose: assert the new settings defaults and enabled module list.
- Create: `tests/core/test_bootstrap_database.py`
  Purpose: verify database initialization and Celery/API bootstrapping behavior.

### Logs Module

- Create: `app/modules/logs/__init__.py`
- Create: `app/modules/logs/module.py`
- Create: `app/modules/logs/messages.py`
- Create: `app/modules/logs/schemas.py`
- Create: `app/modules/logs/repository.py`
- Create: `app/modules/logs/services.py`
- Create: `app/modules/logs/jobs.py`
- Create: `app/modules/logs/api.py`
  Purpose: accept `POST /logs/ingest`, persist logs synchronously, expose `GET /logs`, and trigger the async pipeline.
- Create: `tests/modules/test_logs_module.py`
  Purpose: cover log persistence, listing, and background pipeline triggering.

### Analysis Module

- Create: `app/modules/analysis/__init__.py`
- Create: `app/modules/analysis/module.py`
- Create: `app/modules/analysis/messages.py`
- Create: `app/modules/analysis/schemas.py`
- Create: `app/modules/analysis/services.py`
- Create: `app/modules/analysis/jobs.py`
  Purpose: cluster similar logs, count occurrences, detect spikes/repeated failures, and dispatch AI analysis only when an anomaly is detected.
- Create: `tests/modules/test_analysis_module.py`
  Purpose: unit-test clustering and anomaly detection rules.

### AI Module

- Create: `app/modules/ai/__init__.py`
- Create: `app/modules/ai/module.py`
- Create: `app/modules/ai/messages.py`
- Create: `app/modules/ai/schemas.py`
- Create: `app/modules/ai/services.py`
- Create: `app/modules/ai/jobs.py`
  Purpose: run structured AI analysis via a configurable OpenAI-compatible HTTP endpoint, with a deterministic fallback analyzer for local/test mode.
- Create: `tests/modules/test_ai_module.py`
  Purpose: cover fallback severity/root-cause generation and JSON response parsing.

### Incident Module

- Create: `app/modules/incident/__init__.py`
- Create: `app/modules/incident/module.py`
- Create: `app/modules/incident/messages.py`
- Create: `app/modules/incident/schemas.py`
- Create: `app/modules/incident/repository.py`
- Create: `app/modules/incident/services.py`
- Create: `app/modules/incident/jobs.py`
- Create: `app/modules/incident/api.py`
  Purpose: create/open incidents from AI output, list incidents, fetch incident details with related logs, and resolve incidents.
- Create: `tests/modules/test_incident_module.py`
  Purpose: cover incident creation, listing, detail expansion, and resolve flows.

### Actions And Alerts

- Create: `app/modules/actions/__init__.py`
- Create: `app/modules/actions/module.py`
- Create: `app/modules/actions/messages.py`
- Create: `app/modules/actions/schemas.py`
- Create: `app/modules/actions/repository.py`
- Create: `app/modules/actions/services.py`
- Create: `app/modules/actions/jobs.py`
- Create: `app/modules/actions/api.py`
  Purpose: persist dashboard actions generated from incidents, list actions, and update action status.
- Create: `app/modules/alerts/__init__.py`
- Create: `app/modules/alerts/module.py`
- Create: `app/modules/alerts/interfaces.py`
  Purpose: placeholder-only interface contracts for future email, Slack, and webhook alert delivery.
- Create: `tests/modules/test_actions_module.py`
- Create: `tests/modules/test_alerts_module.py`
- Create: `tests/integration/test_log_pipeline.py`
  Purpose: verify action CRUD, placeholder contracts, and the full logs → analysis → AI → incident → action flow.

---

### Task 1: Wire Startup, Settings, And SQLite Schema

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/core/bootstrap.py`
- Modify: `app/core/celery_app.py`
- Modify: `app/main.py`
- Modify: `.env.example`
- Modify: `tests/conftest.py`
- Modify: `tests/core/test_config.py`
- Create: `app/core/database.py`
- Create: `tests/core/test_bootstrap_database.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from celery import Celery
from fastapi import FastAPI

from app.core.bootstrap import bootstrap_app, bootstrap_celery_tasks
from app.core.config import Settings
from app.core.database import initialize_database


class DummyModule:
    name = "dummy"

    def __init__(self) -> None:
        self.router_registered = False
        self.task_registered = False

    def register_routes(self):
        from fastapi import APIRouter

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


def test_settings_load_logsense_defaults() -> None:
    settings = Settings()

    assert settings.sqlite_database_path == "data/logsense.db"
    assert settings.analysis_window_minutes == 15
    assert settings.error_frequency_threshold == 5
    assert settings.spike_multiplier == 2.0
    assert settings.enabled_modules == [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
    ]


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/core/test_config.py tests/core/test_bootstrap_database.py -v --no-cov`
Expected: FAIL because `sqlite_database_path`, `bootstrap_celery_tasks`, and `initialize_database` do not exist yet, and the enabled module list still references `app.modules.jobs.module`.

- [ ] **Step 3: Write the minimal implementation**

```python
# app/core/config.py
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
    sqlite_database_path: str = "data/logsense.db"
    analysis_window_minutes: int = 15
    error_frequency_threshold: int = 5
    spike_multiplier: float = 2.0
    llm_enabled: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 20
    enabled_modules: list[str] = Field(
        default_factory=lambda: [
            "app.modules.health.module",
            "app.modules.auth.module",
            "app.modules.email.module",
            "app.modules.system.module",
        ]
    )
    auto_discover_modules: bool = True
```

```python
# app/core/database.py
from pathlib import Path
import sqlite3

from app.core.config import Settings


def get_connection(*, settings: Settings) -> sqlite3.Connection:
    Path(settings.sqlite_database_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.sqlite_database_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(*, settings: Settings) -> None:
    with get_connection(settings=settings) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                service TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                suggested_action TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS actions (
                id TEXT PRIMARY KEY,
                incident_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents (id)
            );

            CREATE INDEX IF NOT EXISTS idx_logs_fingerprint_timestamp
            ON logs (fingerprint, timestamp);

            CREATE INDEX IF NOT EXISTS idx_incidents_fingerprint_status
            ON incidents (fingerprint, status);

            CREATE INDEX IF NOT EXISTS idx_actions_incident_id
            ON actions (incident_id);
            """
        )
```

```python
# app/core/bootstrap.py
from collections.abc import Sequence

from celery import Celery
from fastapi import FastAPI

from app.core.config import Settings
from app.core.registry import ModuleContract, ModuleRegistry


def load_modules(*, settings: Settings) -> list[ModuleContract]:
    registry = ModuleRegistry(settings=settings)
    return registry.load_modules()


def bootstrap_app(*, app: FastAPI, settings: Settings) -> Sequence[ModuleContract]:
    modules = load_modules(settings=settings)
    for module in modules:
        app.include_router(module.register_routes(), prefix=settings.api_prefix)
    return modules


def bootstrap_celery_tasks(*, celery_app: Celery, settings: Settings) -> list[object]:
    registered_tasks: list[object] = []
    for module in load_modules(settings=settings):
        for task in module.register_tasks():
            celery_app.tasks.register(task)
            registered_tasks.append(task)
    return registered_tasks
```

```python
# app/core/celery_app.py
from celery import Celery

from app.core.bootstrap import bootstrap_celery_tasks
from app.core.config import Settings
from app.core.database import initialize_database


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
initialize_database(settings=settings)
bootstrap_celery_tasks(celery_app=celery_app, settings=settings)
```

```python
# app/main.py
from fastapi import FastAPI

from app.core.bootstrap import bootstrap_app
from app.core.config import Settings
from app.core.database import initialize_database
from app.core.logging import configure_logging
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    configure_logging()
    initialize_database(settings=resolved_settings)
    app = FastAPI(title=resolved_settings.app_name, debug=resolved_settings.debug)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware, settings=resolved_settings)
    register_exception_handlers(app)
    bootstrap_app(app=app, settings=resolved_settings)
    return app


app = create_app()
```

```env
# .env.example
APP_NAME=pipeline-execution
ENVIRONMENT=local
DEBUG=false
API_PREFIX=/api/v1
API_KEY=local-dev-key
REDIS_URL=redis://redis:6379/0
RESULT_BACKEND_URL=redis://redis:6379/1
SQLITE_DATABASE_PATH=data/logsense.db
ANALYSIS_WINDOW_MINUTES=15
ERROR_FREQUENCY_THRESHOLD=5
SPIKE_MULTIPLIER=2.0
LLM_ENABLED=false
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=
LLM_MODEL=gpt-4.1-mini
LLM_TIMEOUT_SECONDS=20
```

```python
# tests/conftest.py
_SETTINGS_ENV_VARS = [
    "APP_NAME",
    "ENVIRONMENT",
    "DEBUG",
    "API_PREFIX",
    "API_KEY",
    "REDIS_URL",
    "RESULT_BACKEND_URL",
    "SQLITE_DATABASE_PATH",
    "ANALYSIS_WINDOW_MINUTES",
    "ERROR_FREQUENCY_THRESHOLD",
    "SPIKE_MULTIPLIER",
    "LLM_ENABLED",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_TIMEOUT_SECONDS",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/core/test_config.py tests/core/test_bootstrap_database.py tests/core/test_registry.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .env.example app/core/config.py app/core/database.py app/core/bootstrap.py app/core/celery_app.py app/main.py tests/conftest.py tests/core/test_config.py tests/core/test_bootstrap_database.py
git commit -m "feat: wire logsense startup and sqlite schema"
```

### Task 2: Add The Logs Ingestion Module

**Files:**
- Create: `app/modules/logs/__init__.py`
- Create: `app/modules/logs/module.py`
- Create: `app/modules/logs/messages.py`
- Create: `app/modules/logs/schemas.py`
- Create: `app/modules/logs/repository.py`
- Create: `app/modules/logs/services.py`
- Create: `app/modules/logs/jobs.py`
- Create: `app/modules/logs/api.py`
- Modify: `app/core/config.py`
- Create: `tests/modules/test_logs_module.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.logs.api import router
from app.modules.logs.jobs import start_log_pipeline_job
from app.modules.logs.repository import LogRepository


def test_ingest_log_persists_record_and_triggers_pipeline(monkeypatch, tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    queued: dict[str, object] = {}

    monkeypatch.setattr(
        "app.modules.logs.api.settings",
        settings,
    )
    monkeypatch.setattr(
        start_log_pipeline_job,
        "delay",
        lambda payload: queued.setdefault("payload", payload) or type("Result", (), {"id": "job-1"})(),
    )

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).post(
        "/api/v1/logs/ingest",
        json={
            "service": "payment",
            "level": "ERROR",
            "message": "Redis timeout after 1500ms",
            "timestamp": "2026-04-05T10:00:00Z",
        },
    )

    repo = LogRepository(settings=settings)
    records = repo.list_logs(limit=10)

    assert response.status_code == 202
    assert response.json()["message_key"] == "logs.ingested"
    assert len(records) == 1
    assert records[0].service == "payment"
    assert "log_id" in queued["payload"]


def test_get_logs_returns_recent_records(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    service = LogRepository(settings=settings)
    service.create_log(
        service="payment",
        level="ERROR",
        message="Redis timeout",
        fingerprint="payment:error:redis-timeout",
        timestamp="2026-04-05T10:00:00Z",
    )

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/logs")

    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["service"] == "payment"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_logs_module.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.logs'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/core/config.py
enabled_modules: list[str] = Field(
    default_factory=lambda: [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
        "app.modules.logs.module",
    ]
)
```

```python
# app/modules/logs/messages.py
class LogMessageKeys:
    INGESTED = "logs.ingested"
    LISTED = "logs.listed"
```

```python
# app/modules/logs/schemas.py
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LogIngestRequest(BaseModel):
    service: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    timestamp: datetime


class LogRecord(BaseModel):
    id: str
    service: str
    level: str
    message: str
    fingerprint: str
    timestamp: str
    created_at: str


class LogListResponse(BaseModel):
    items: list[LogRecord]
```

```python
# app/modules/logs/jobs.py
from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app


class StartLogPipelineJob(BaseJob):
    name = "logs.start_pipeline"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"message_key": "logs.ingested", "log_id": payload["log_id"], "fingerprint": payload["fingerprint"]}


job = StartLogPipelineJob(celery_app=celery_app)


@celery_app.task(bind=True, name="logs.start_pipeline")
def start_log_pipeline_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
```

```python
# app/modules/logs/repository.py
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_connection
from app.modules.logs.schemas import LogRecord


class LogRepository:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def create_log(
        self,
        *,
        service: str,
        level: str,
        message: str,
        fingerprint: str,
        timestamp: str,
    ) -> LogRecord:
        record = LogRecord(
            id=f"LOG-{uuid4().hex[:12]}",
            service=service,
            level=level,
            message=message,
            fingerprint=fingerprint,
            timestamp=timestamp,
            created_at=datetime.now(UTC).isoformat(),
        )
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                INSERT INTO logs (id, service, level, message, fingerprint, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.service,
                    record.level,
                    record.message,
                    record.fingerprint,
                    record.timestamp,
                    record.created_at,
                ),
            )
        return record

    def list_logs(self, *, limit: int) -> list[LogRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, service, level, message, fingerprint, timestamp, created_at
                FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [LogRecord.model_validate(dict(row)) for row in rows]

    def list_by_fingerprint(self, *, fingerprint: str, limit: int) -> list[LogRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, service, level, message, fingerprint, timestamp, created_at
                FROM logs
                WHERE fingerprint = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (fingerprint, limit),
            ).fetchall()
        return [LogRecord.model_validate(dict(row)) for row in rows]
```

```python
# app/modules/logs/services.py
import hashlib
import re

from app.core.config import Settings
from app.modules.logs.repository import LogRepository
from app.modules.logs.schemas import LogIngestRequest, LogListResponse, LogRecord


class LogService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.repository = LogRepository(settings=settings)

    def build_fingerprint(self, *, service: str, level: str, message: str) -> str:
        normalized_message = re.sub(r"\d+", "<num>", message.lower()).strip()
        digest = hashlib.sha1(f"{service}:{level}:{normalized_message}".encode()).hexdigest()[:16]
        return f"{service}:{level}:{digest}"

    def ingest(self, payload: LogIngestRequest) -> LogRecord:
        fingerprint = self.build_fingerprint(
            service=payload.service,
            level=payload.level,
            message=payload.message,
        )
        return self.repository.create_log(
            service=payload.service,
            level=payload.level,
            message=payload.message,
            fingerprint=fingerprint,
            timestamp=payload.timestamp.isoformat(),
        )

    def list_logs(self) -> LogListResponse:
        return LogListResponse(items=self.repository.list_logs(limit=100))
```

```python
# app/modules/logs/api.py
from fastapi import APIRouter, status

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.logs.jobs import start_log_pipeline_job
from app.modules.logs.messages import LogMessageKeys
from app.modules.logs.schemas import LogIngestRequest
from app.modules.logs.services import LogService

router = APIRouter(tags=["logs"])
settings = Settings()
service = LogService(settings=settings)


@router.post("/logs/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_logs(payload: LogIngestRequest) -> dict[str, object]:
    record = service.ingest(payload)
    async_result = start_log_pipeline_job.delay({"log_id": record.id, "fingerprint": record.fingerprint})
    return success_response(
        message="Log ingested and pipeline triggered",
        message_key=LogMessageKeys.INGESTED,
        data={"log": record.model_dump(), "task_id": async_result.id},
    )


@router.get("/logs")
def list_logs() -> dict[str, object]:
    return success_response(
        message="Logs retrieved",
        message_key=LogMessageKeys.LISTED,
        data=service.list_logs().model_dump(),
    )
```

```python
# app/modules/logs/module.py
from fastapi import APIRouter


class Module:
    name = "logs"

    def register_routes(self) -> APIRouter:
        from app.modules.logs.api import router

        return router

    def register_tasks(self) -> list[object]:
        from app.modules.logs.jobs import start_log_pipeline_job

        return [start_log_pipeline_job]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_logs_module.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/modules/logs tests/modules/test_logs_module.py
git commit -m "feat: add log ingestion module"
```

### Task 3: Implement Clustering And Anomaly Detection Jobs

**Files:**
- Create: `app/modules/analysis/__init__.py`
- Create: `app/modules/analysis/module.py`
- Create: `app/modules/analysis/messages.py`
- Create: `app/modules/analysis/schemas.py`
- Create: `app/modules/analysis/services.py`
- Create: `app/modules/analysis/jobs.py`
- Modify: `app/modules/logs/jobs.py`
- Modify: `app/core/config.py`
- Create: `tests/modules/test_analysis_module.py`

- [ ] **Step 1: Write the failing test**

```python
from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.analysis.schemas import ClusterSummary
from app.modules.analysis.services import AnalysisService
from app.modules.logs.repository import LogRepository


def test_analysis_service_clusters_similar_logs_and_detects_frequency(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        error_frequency_threshold=3,
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    logs = LogRepository(settings=settings)
    for index in range(3):
        logs.create_log(
            service="payment",
            level="ERROR",
            message=f"Redis timeout after {index + 1} attempts",
            fingerprint="payment:ERROR:redis-timeout",
            timestamp=f"2026-04-05T10:0{index}:00+00:00",
        )

    service = AnalysisService(settings=settings)
    summary = service.build_cluster_summary(log_id=None, fingerprint="payment:ERROR:redis-timeout")
    decision = service.detect_anomaly(summary)

    assert isinstance(summary, ClusterSummary)
    assert summary.occurrence_count == 3
    assert decision.triggered is True
    assert "high_frequency_errors" in decision.reasons
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_analysis_module.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.analysis'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/core/config.py
enabled_modules: list[str] = Field(
    default_factory=lambda: [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
        "app.modules.logs.module",
        "app.modules.analysis.module",
    ]
)
```

```python
# app/modules/analysis/messages.py
class AnalysisMessageKeys:
    CLUSTERED = "analysis.clustered"
    ANOMALY_DETECTED = "analysis.anomaly_detected"
    NO_ANOMALY = "analysis.no_anomaly"
```

```python
# app/modules/analysis/schemas.py
from pydantic import BaseModel


class ClusterSummary(BaseModel):
    fingerprint: str
    service: str
    level: str
    sample_message: str
    occurrence_count: int
    first_seen: str
    last_seen: str


class AnomalyDecision(BaseModel):
    triggered: bool
    reasons: list[str]
```

```python
# app/modules/analysis/services.py
from app.core.config import Settings
from app.modules.analysis.schemas import AnomalyDecision, ClusterSummary
from app.modules.logs.repository import LogRepository


class AnalysisService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.log_repository = LogRepository(settings=settings)

    def build_cluster_summary(self, *, log_id: str | None, fingerprint: str) -> ClusterSummary:
        records = self.log_repository.list_by_fingerprint(fingerprint=fingerprint, limit=100)
        latest = records[0]
        oldest = records[-1]
        return ClusterSummary(
            fingerprint=fingerprint,
            service=latest.service,
            level=latest.level,
            sample_message=latest.message,
            occurrence_count=len(records),
            first_seen=oldest.timestamp,
            last_seen=latest.timestamp,
        )

    def detect_anomaly(self, summary: ClusterSummary) -> AnomalyDecision:
        reasons: list[str] = []
        if summary.level == "ERROR" and summary.occurrence_count >= self.settings.error_frequency_threshold:
            reasons.append("high_frequency_errors")
        if summary.occurrence_count >= int(self.settings.error_frequency_threshold * self.settings.spike_multiplier):
            reasons.append("sudden_spike")
        if summary.level in {"ERROR", "CRITICAL"} and summary.occurrence_count >= 2:
            reasons.append("repeated_failures")
        return AnomalyDecision(triggered=bool(reasons), reasons=reasons)
```

```python
# app/modules/logs/jobs.py
class StartLogPipelineJob(BaseJob):
    name = "logs.start_pipeline"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        from app.modules.analysis.jobs import cluster_logs_job

        cluster_logs_job.delay(payload)
        return {"message_key": "logs.ingested", "log_id": payload["log_id"], "fingerprint": payload["fingerprint"]}
```

```python
# app/modules/analysis/jobs.py
from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.analysis.services import AnalysisService
from app.modules.analysis.schemas import ClusterSummary

settings = Settings()


class ClusterLogsJob(BaseJob):
    name = "analysis.cluster_logs"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = AnalysisService(settings=settings)
        summary = service.build_cluster_summary(
            log_id=payload.get("log_id"),
            fingerprint=str(payload["fingerprint"]),
        )
        detect_anomalies_job.delay({"cluster": summary.model_dump()})
        return {"message_key": "analysis.clustered", "cluster": summary.model_dump()}


class DetectAnomaliesJob(BaseJob):
    name = "analysis.detect_anomalies"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = AnalysisService(settings=settings)
        cluster = ClusterSummary.model_validate(payload["cluster"])
        decision = service.detect_anomaly(cluster)
        if decision.triggered:
            from app.modules.ai.jobs import ai_analysis_job

            ai_analysis_job.delay(
                {
                    "cluster": cluster.model_dump(),
                    "reasons": decision.reasons,
                }
            )
        return {
            "message_key": "analysis.anomaly_detected" if decision.triggered else "analysis.no_anomaly",
            "cluster": cluster.model_dump(),
            "decision": decision.model_dump(),
        }


cluster_job = ClusterLogsJob(celery_app=celery_app)
detect_job = DetectAnomaliesJob(celery_app=celery_app)


@celery_app.task(bind=True, name="analysis.cluster_logs")
def cluster_logs_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return cluster_job.execute(payload)


@celery_app.task(bind=True, name="analysis.detect_anomalies")
def detect_anomalies_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return detect_job.execute(payload)
```

```python
# app/modules/analysis/module.py
from fastapi import APIRouter

from app.modules.analysis.jobs import cluster_logs_job, detect_anomalies_job


class Module:
    name = "analysis"

    def register_routes(self) -> APIRouter:
        return APIRouter(tags=["analysis"])

    def register_tasks(self) -> list[object]:
        return [cluster_logs_job, detect_anomalies_job]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_analysis_module.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/modules/logs/jobs.py app/modules/analysis tests/modules/test_analysis_module.py
git commit -m "feat: add clustering and anomaly detection jobs"
```

### Task 4: Add Structured AI Analysis With Fallback Logic

**Files:**
- Create: `app/modules/ai/__init__.py`
- Create: `app/modules/ai/module.py`
- Create: `app/modules/ai/messages.py`
- Create: `app/modules/ai/schemas.py`
- Create: `app/modules/ai/services.py`
- Create: `app/modules/ai/jobs.py`
- Modify: `app/core/config.py`
- Create: `tests/modules/test_ai_module.py`

- [ ] **Step 1: Write the failing test**

```python
import json

import httpx

from app.core.config import Settings
from app.modules.ai.schemas import AIAnalysisRequest
from app.modules.ai.services import AIService


def test_ai_service_uses_fallback_when_llm_disabled() -> None:
    settings = Settings(llm_enabled=False, auto_discover_modules=False)
    service = AIService(settings=settings, client=httpx.Client())

    result = service.analyze(
        AIAnalysisRequest(
            fingerprint="payment:ERROR:abc123",
            service="payment",
            level="ERROR",
            sample_message="Redis timeout after 3 attempts",
            occurrence_count=6,
            reasons=["high_frequency_errors", "repeated_failures"],
        )
    )

    assert result.severity == "high"
    assert "Redis timeout" in result.root_cause
    assert result.suggested_action != ""


def test_ai_service_parses_llm_json_response(monkeypatch) -> None:
    settings = Settings(
        llm_enabled=True,
        llm_api_key="test-key",
        auto_discover_modules=False,
    )

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "title": "Redis failures detected",
                                    "root_cause": "Redis connection pool exhausted",
                                    "severity": "high",
                                    "fix_suggestion": "Increase pool size or add retry logic",
                                }
                            )
                        }
                    }
                ]
            }

    client = httpx.Client()
    monkeypatch.setattr(client, "post", lambda *args, **kwargs: DummyResponse())
    service = AIService(settings=settings, client=client)

    result = service.analyze(
        AIAnalysisRequest(
            fingerprint="payment:ERROR:abc123",
            service="payment",
            level="ERROR",
            sample_message="Redis timeout after 3 attempts",
            occurrence_count=6,
            reasons=["high_frequency_errors"],
        )
    )

    assert result.root_cause == "Redis connection pool exhausted"
    assert result.suggested_action == "Increase pool size or add retry logic"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_ai_module.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.ai'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/core/config.py
enabled_modules: list[str] = Field(
    default_factory=lambda: [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
        "app.modules.logs.module",
        "app.modules.analysis.module",
        "app.modules.ai.module",
    ]
)
```

```python
# app/modules/ai/messages.py
class AIMessageKeys:
    ANALYSIS_COMPLETED = "ai.analysis_completed"
```

```python
# app/modules/ai/schemas.py
from pydantic import BaseModel


class AIAnalysisRequest(BaseModel):
    fingerprint: str
    service: str
    level: str
    sample_message: str
    occurrence_count: int
    reasons: list[str]


class AIAnalysisResult(BaseModel):
    fingerprint: str
    title: str
    root_cause: str
    severity: str
    suggested_action: str
```

```python
# app/modules/ai/services.py
import json

import httpx

from app.core.config import Settings
from app.modules.ai.schemas import AIAnalysisRequest, AIAnalysisResult


class AIService:
    def __init__(self, *, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.llm_timeout_seconds)

    def fallback_analysis(self, payload: AIAnalysisRequest) -> AIAnalysisResult:
        severity = "high" if payload.level == "ERROR" and payload.occurrence_count >= 5 else "medium"
        return AIAnalysisResult(
            fingerprint=payload.fingerprint,
            title=f"{payload.service.title()} failures detected",
            root_cause=payload.sample_message,
            severity=severity,
            suggested_action="Inspect connection limits, add retries, and verify downstream health.",
        )

    def analyze(self, payload: AIAnalysisRequest) -> AIAnalysisResult:
        if not self.settings.llm_enabled or not self.settings.llm_api_key:
            return self.fallback_analysis(payload)

        response = self.client.post(
            f"{self.settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
            json={
                "model": self.settings.llm_model,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return strict JSON with title, root_cause, severity, and fix_suggestion. "
                            "Severity must be low, medium, or high."
                        ),
                    },
                    {"role": "user", "content": payload.model_dump_json()},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return AIAnalysisResult(
            fingerprint=payload.fingerprint,
            title=parsed["title"],
            root_cause=parsed["root_cause"],
            severity=parsed["severity"],
            suggested_action=parsed["fix_suggestion"],
        )
```

```python
# app/modules/ai/jobs.py
from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.ai.schemas import AIAnalysisRequest
from app.modules.ai.services import AIService

settings = Settings()


class AIAnalysisJob(BaseJob):
    name = "ai.analysis"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = AIService(settings=settings)
        request = AIAnalysisRequest(
            **payload["cluster"],
            reasons=list(payload["reasons"]),
        )
        result = service.analyze(request)
        from app.modules.incident.jobs import create_incident_job

        create_incident_job.delay(result.model_dump())
        return {"message_key": "ai.analysis_completed", "analysis": result.model_dump()}


job = AIAnalysisJob(celery_app=celery_app)


@celery_app.task(bind=True, name="ai.analysis")
def ai_analysis_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
```

```python
# app/modules/ai/module.py
from fastapi import APIRouter

from app.modules.ai.jobs import ai_analysis_job


class Module:
    name = "ai"

    def register_routes(self) -> APIRouter:
        return APIRouter(tags=["ai"])

    def register_tasks(self) -> list[object]:
        return [ai_analysis_job]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_ai_module.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/modules/ai tests/modules/test_ai_module.py
git commit -m "feat: add ai analysis service"
```

### Task 5: Build Incidents And Dashboard APIs

**Files:**
- Create: `app/modules/incident/__init__.py`
- Create: `app/modules/incident/module.py`
- Create: `app/modules/incident/messages.py`
- Create: `app/modules/incident/schemas.py`
- Create: `app/modules/incident/repository.py`
- Create: `app/modules/incident/services.py`
- Create: `app/modules/incident/jobs.py`
- Create: `app/modules/incident/api.py`
- Modify: `app/core/config.py`
- Create: `tests/modules/test_incident_module.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.incident.api import router
from app.modules.incident.services import IncidentService
from app.modules.logs.repository import LogRepository


def test_incident_service_creates_and_resolves_incident(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    logs = LogRepository(settings=settings)
    logs.create_log(
        service="payment",
        level="ERROR",
        message="Redis timeout",
        fingerprint="payment:ERROR:redis-timeout",
        timestamp="2026-04-05T10:00:00+00:00",
    )

    service = IncidentService(settings=settings)
    incident = service.create_incident(
        fingerprint="payment:ERROR:redis-timeout",
        title="Redis failures detected",
        severity="high",
        root_cause="Redis connection pool exhausted",
        suggested_action="Increase Redis pool size",
    )
    resolved = service.resolve_incident(incident.id)

    assert incident.status == "open"
    assert resolved.status == "resolved"


def test_incident_api_returns_detail_with_related_logs(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    service = IncidentService(settings=settings)
    incident = service.create_incident(
        fingerprint="payment:ERROR:redis-timeout",
        title="Redis failures detected",
        severity="high",
        root_cause="Redis connection pool exhausted",
        suggested_action="Increase Redis pool size",
    )

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get(f"/api/v1/incidents/{incident.id}")

    assert response.status_code == 200
    assert response.json()["message_key"] == "incident.detail"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/modules/test_incident_module.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.incident'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/core/config.py
enabled_modules: list[str] = Field(
    default_factory=lambda: [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
        "app.modules.logs.module",
        "app.modules.analysis.module",
        "app.modules.ai.module",
        "app.modules.incident.module",
    ]
)
```

```python
# app/modules/incident/messages.py
class IncidentMessageKeys:
    CREATED = "incident.created"
    LISTED = "incident.listed"
    DETAIL = "incident.detail"
    RESOLVED = "incident.resolved"
```

```python
# app/modules/incident/schemas.py
from pydantic import BaseModel

from app.modules.logs.schemas import LogRecord


class IncidentRecord(BaseModel):
    id: str
    fingerprint: str
    title: str
    severity: str
    status: str
    root_cause: str
    suggested_action: str
    created_at: str
    updated_at: str
    resolved_at: str | None = None


class IncidentListResponse(BaseModel):
    items: list[IncidentRecord]


class IncidentDetail(BaseModel):
    incident: IncidentRecord
    logs: list[LogRecord]
```

```python
# app/modules/incident/repository.py
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_connection
from app.modules.incident.schemas import IncidentRecord


class IncidentRepository:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def create_incident(
        self,
        *,
        fingerprint: str,
        title: str,
        severity: str,
        root_cause: str,
        suggested_action: str,
    ) -> IncidentRecord:
        now = datetime.now(UTC).isoformat()
        incident = IncidentRecord(
            id=f"INC-{uuid4().hex[:8].upper()}",
            fingerprint=fingerprint,
            title=title,
            severity=severity,
            status="open",
            root_cause=root_cause,
            suggested_action=suggested_action,
            created_at=now,
            updated_at=now,
            resolved_at=None,
        )
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                INSERT INTO incidents (
                    id, fingerprint, title, severity, status, root_cause,
                    suggested_action, created_at, updated_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.fingerprint,
                    incident.title,
                    incident.severity,
                    incident.status,
                    incident.root_cause,
                    incident.suggested_action,
                    incident.created_at,
                    incident.updated_at,
                    incident.resolved_at,
                ),
            )
        return incident

    def list_incidents(self) -> list[IncidentRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, fingerprint, title, severity, status, root_cause,
                       suggested_action, created_at, updated_at, resolved_at
                FROM incidents
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [IncidentRecord.model_validate(dict(row)) for row in rows]

    def get_incident(self, incident_id: str) -> IncidentRecord:
        with get_connection(settings=self.settings) as connection:
            row = connection.execute(
                """
                SELECT id, fingerprint, title, severity, status, root_cause,
                       suggested_action, created_at, updated_at, resolved_at
                FROM incidents
                WHERE id = ?
                """,
                (incident_id,),
            ).fetchone()
        return IncidentRecord.model_validate(dict(row))

    def resolve_incident(self, incident_id: str) -> IncidentRecord:
        now = datetime.now(UTC).isoformat()
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                UPDATE incidents
                SET status = 'resolved', updated_at = ?, resolved_at = ?
                WHERE id = ?
                """,
                (now, now, incident_id),
            )
        return self.get_incident(incident_id)
```

```python
# app/modules/incident/services.py
from app.core.config import Settings
from app.modules.incident.repository import IncidentRepository
from app.modules.incident.schemas import IncidentDetail, IncidentListResponse, IncidentRecord
from app.modules.logs.repository import LogRepository


class IncidentService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.repository = IncidentRepository(settings=settings)
        self.log_repository = LogRepository(settings=settings)

    def create_incident(
        self,
        *,
        fingerprint: str,
        title: str,
        severity: str,
        root_cause: str,
        suggested_action: str,
    ) -> IncidentRecord:
        return self.repository.create_incident(
            fingerprint=fingerprint,
            title=title,
            severity=severity,
            root_cause=root_cause,
            suggested_action=suggested_action,
        )

    def list_incidents(self) -> IncidentListResponse:
        return IncidentListResponse(items=self.repository.list_incidents())

    def get_incident_detail(self, incident_id: str) -> IncidentDetail:
        incident = self.repository.get_incident(incident_id)
        return IncidentDetail(
            incident=incident,
            logs=self.log_repository.list_by_fingerprint(fingerprint=incident.fingerprint, limit=50),
        )

    def resolve_incident(self, incident_id: str) -> IncidentRecord:
        return self.repository.resolve_incident(incident_id)
```

```python
# app/modules/incident/jobs.py
from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.incident.services import IncidentService

settings = Settings()


class CreateIncidentJob(BaseJob):
    name = "incident.create"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = IncidentService(settings=settings)
        incident = service.create_incident(
            fingerprint=str(payload["fingerprint"]),
            title=str(payload["title"]),
            severity=str(payload["severity"]),
            root_cause=str(payload["root_cause"]),
            suggested_action=str(payload["suggested_action"]),
        )
        from app.modules.actions.jobs import store_action_job

        store_action_job.delay(
            {
                "incident_id": incident.id,
                "title": incident.title,
                "description": incident.suggested_action,
            }
        )
        return {"message_key": "incident.created", "incident": incident.model_dump()}


job = CreateIncidentJob(celery_app=celery_app)


@celery_app.task(bind=True, name="incident.create")
def create_incident_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
```

```python
# app/modules/incident/api.py
from fastapi import APIRouter

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.incident.messages import IncidentMessageKeys
from app.modules.incident.services import IncidentService

router = APIRouter(tags=["incident"])
service = IncidentService(settings=Settings())


@router.get("/incidents")
def list_incidents() -> dict[str, object]:
    return success_response(
        message="Incidents retrieved",
        message_key=IncidentMessageKeys.LISTED,
        data=service.list_incidents().model_dump(),
    )


@router.get("/incidents/{incident_id}")
def incident_detail(incident_id: str) -> dict[str, object]:
    return success_response(
        message="Incident detail retrieved",
        message_key=IncidentMessageKeys.DETAIL,
        data=service.get_incident_detail(incident_id).model_dump(),
    )


@router.patch("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str) -> dict[str, object]:
    return success_response(
        message="Incident resolved",
        message_key=IncidentMessageKeys.RESOLVED,
        data=service.resolve_incident(incident_id).model_dump(),
    )
```

```python
# app/modules/incident/module.py
from fastapi import APIRouter

from app.modules.incident.jobs import create_incident_job


class Module:
    name = "incident"

    def register_routes(self) -> APIRouter:
        from app.modules.incident.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [create_incident_job]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/modules/test_incident_module.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/modules/incident tests/modules/test_incident_module.py
git commit -m "feat: add incident dashboard module"
```

### Task 6: Add Actions, Alert Placeholders, And End-To-End Pipeline Coverage

**Files:**
- Create: `app/modules/actions/__init__.py`
- Create: `app/modules/actions/module.py`
- Create: `app/modules/actions/messages.py`
- Create: `app/modules/actions/schemas.py`
- Create: `app/modules/actions/repository.py`
- Create: `app/modules/actions/services.py`
- Create: `app/modules/actions/jobs.py`
- Create: `app/modules/actions/api.py`
- Create: `app/modules/alerts/__init__.py`
- Create: `app/modules/alerts/module.py`
- Create: `app/modules/alerts/interfaces.py`
- Modify: `app/core/config.py`
- Create: `tests/modules/test_actions_module.py`
- Create: `tests/modules/test_alerts_module.py`
- Create: `tests/integration/test_log_pipeline.py`

- [ ] **Step 1: Write the failing tests**

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.actions.api import router as actions_router
from app.modules.actions.services import ActionService
from app.modules.alerts.interfaces import AlertDispatcher
from app.modules.logs.api import router as logs_router


def test_action_api_lists_and_updates_status(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    service = ActionService(settings=settings)
    action = service.create_action(
        incident_id="INC-123",
        title="Increase Redis pool size",
        description="Increase Redis pool size or add retry logic",
    )

    app = FastAPI()
    app.include_router(actions_router, prefix="/api/v1")
    client = TestClient(app)

    listed = client.get("/api/v1/actions")
    updated = client.patch(f"/api/v1/actions/{action.id}", json={"status": "completed"})

    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["title"] == "Increase Redis pool size"
    assert updated.json()["data"]["status"] == "completed"


def test_alert_dispatcher_contract_is_placeholder_only() -> None:
    assert hasattr(AlertDispatcher, "send_incident")


def test_full_log_pipeline_creates_incident_and_action(monkeypatch, tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        error_frequency_threshold=1,
        llm_enabled=False,
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)

    monkeypatch.setattr("app.modules.logs.api.settings", settings)
    monkeypatch.setattr("app.modules.logs.api.service.settings", settings)
    monkeypatch.setattr("app.modules.analysis.jobs.settings", settings)
    monkeypatch.setattr("app.modules.ai.jobs.settings", settings)
    monkeypatch.setattr("app.modules.incident.jobs.settings", settings)
    monkeypatch.setattr("app.modules.actions.jobs.settings", settings)

    monkeypatch.setattr(
        "app.modules.analysis.jobs.cluster_logs_job.delay",
        lambda payload: __import__("app.modules.analysis.jobs", fromlist=["cluster_logs_job"]).cluster_job.execute(payload),
    )
    monkeypatch.setattr(
        "app.modules.analysis.jobs.detect_anomalies_job.delay",
        lambda payload: __import__("app.modules.analysis.jobs", fromlist=["detect_anomalies_job"]).detect_job.execute(payload),
    )
    monkeypatch.setattr(
        "app.modules.ai.jobs.ai_analysis_job.delay",
        lambda payload: __import__("app.modules.ai.jobs", fromlist=["ai_analysis_job"]).job.execute(payload),
    )
    monkeypatch.setattr(
        "app.modules.incident.jobs.create_incident_job.delay",
        lambda payload: __import__("app.modules.incident.jobs", fromlist=["create_incident_job"]).job.execute(payload),
    )
    monkeypatch.setattr(
        "app.modules.actions.jobs.store_action_job.delay",
        lambda payload: __import__("app.modules.actions.jobs", fromlist=["store_action_job"]).job.execute(payload),
    )

    app = FastAPI()
    app.include_router(logs_router, prefix="/api/v1")
    client = TestClient(app)
    response = client.post(
        "/api/v1/logs/ingest",
        json={
            "service": "payment",
            "level": "ERROR",
            "message": "Redis timeout after 3 attempts",
            "timestamp": "2026-04-05T10:00:00Z",
        },
    )

    assert response.status_code == 202
    action_service = ActionService(settings=settings)
    assert action_service.list_actions().items[0].status == "open"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/modules/test_actions_module.py tests/modules/test_alerts_module.py tests/integration/test_log_pipeline.py -v --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.actions'`

- [ ] **Step 3: Write the minimal implementation**

```python
# app/core/config.py
enabled_modules: list[str] = Field(
    default_factory=lambda: [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
        "app.modules.logs.module",
        "app.modules.analysis.module",
        "app.modules.ai.module",
        "app.modules.incident.module",
        "app.modules.actions.module",
        "app.modules.alerts.module",
    ]
)
```

```python
# app/modules/actions/messages.py
class ActionMessageKeys:
    LISTED = "actions.listed"
    UPDATED = "actions.updated"
    CREATED = "incident.action_created"
```

```python
# app/modules/actions/schemas.py
from typing import Literal

from pydantic import BaseModel


class ActionRecord(BaseModel):
    id: str
    incident_id: str
    title: str
    description: str
    status: Literal["open", "completed"]
    created_at: str
    updated_at: str


class ActionListResponse(BaseModel):
    items: list[ActionRecord]


class ActionUpdateRequest(BaseModel):
    status: Literal["open", "completed"]
```

```python
# app/modules/actions/repository.py
from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_connection
from app.modules.actions.schemas import ActionRecord


class ActionRepository:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def create_action(self, *, incident_id: str, title: str, description: str) -> ActionRecord:
        now = datetime.now(UTC).isoformat()
        action = ActionRecord(
            id=f"ACT-{uuid4().hex[:8].upper()}",
            incident_id=incident_id,
            title=title,
            description=description,
            status="open",
            created_at=now,
            updated_at=now,
        )
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                INSERT INTO actions (id, incident_id, title, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action.id,
                    action.incident_id,
                    action.title,
                    action.description,
                    action.status,
                    action.created_at,
                    action.updated_at,
                ),
            )
        return action

    def list_actions(self) -> list[ActionRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, incident_id, title, description, status, created_at, updated_at
                FROM actions
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [ActionRecord.model_validate(dict(row)) for row in rows]

    def update_status(self, action_id: str, status: str) -> ActionRecord:
        now = datetime.now(UTC).isoformat()
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                UPDATE actions SET status = ?, updated_at = ? WHERE id = ?
                """,
                (status, now, action_id),
            )
            row = connection.execute(
                """
                SELECT id, incident_id, title, description, status, created_at, updated_at
                FROM actions
                WHERE id = ?
                """,
                (action_id,),
            ).fetchone()
        return ActionRecord.model_validate(dict(row))
```

```python
# app/modules/actions/services.py
from app.core.config import Settings
from app.modules.actions.repository import ActionRepository
from app.modules.actions.schemas import ActionListResponse, ActionRecord


class ActionService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.repository = ActionRepository(settings=settings)

    def create_action(self, *, incident_id: str, title: str, description: str) -> ActionRecord:
        return self.repository.create_action(
            incident_id=incident_id,
            title=title,
            description=description,
        )

    def list_actions(self) -> ActionListResponse:
        return ActionListResponse(items=self.repository.list_actions())

    def update_status(self, action_id: str, status: str) -> ActionRecord:
        return self.repository.update_status(action_id, status)
```

```python
# app/modules/actions/jobs.py
from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.actions.services import ActionService

settings = Settings()


class StoreActionJob(BaseJob):
    name = "actions.store"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = ActionService(settings=settings)
        action = service.create_action(
            incident_id=str(payload["incident_id"]),
            title=str(payload["title"]),
            description=str(payload["description"]),
        )
        return {"message_key": "incident.action_created", "action": action.model_dump()}


job = StoreActionJob(celery_app=celery_app)


@celery_app.task(bind=True, name="actions.store")
def store_action_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return job.execute(payload)
```

```python
# app/modules/actions/api.py
from fastapi import APIRouter

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.actions.messages import ActionMessageKeys
from app.modules.actions.schemas import ActionUpdateRequest
from app.modules.actions.services import ActionService

router = APIRouter(tags=["actions"])
service = ActionService(settings=Settings())


@router.get("/actions")
def list_actions() -> dict[str, object]:
    return success_response(
        message="Actions retrieved",
        message_key=ActionMessageKeys.LISTED,
        data=service.list_actions().model_dump(),
    )


@router.patch("/actions/{action_id}")
def update_action(action_id: str, payload: ActionUpdateRequest) -> dict[str, object]:
    return success_response(
        message="Action updated",
        message_key=ActionMessageKeys.UPDATED,
        data=service.update_status(action_id, payload.status).model_dump(),
    )
```

```python
# app/modules/actions/module.py
from fastapi import APIRouter

from app.modules.actions.jobs import store_action_job


class Module:
    name = "actions"

    def register_routes(self) -> APIRouter:
        from app.modules.actions.api import router

        return router

    def register_tasks(self) -> list[object]:
        return [store_action_job]
```

```python
# app/modules/alerts/interfaces.py
from typing import Protocol


class AlertDispatcher(Protocol):
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None: ...


class EmailAlertDispatcher:
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None:
        raise NotImplementedError("Email alert delivery is out of scope for the MVP")


class SlackAlertDispatcher:
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None:
        raise NotImplementedError("Slack alert delivery is out of scope for the MVP")


class WebhookAlertDispatcher:
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None:
        raise NotImplementedError("Webhook alert delivery is out of scope for the MVP")
```

```python
# app/modules/alerts/module.py
from fastapi import APIRouter


class Module:
    name = "alerts"

    def register_routes(self) -> APIRouter:
        return APIRouter(tags=["alerts"])

    def register_tasks(self) -> list[object]:
        return []
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/modules/test_actions_module.py tests/modules/test_alerts_module.py tests/integration/test_log_pipeline.py -v --no-cov`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/modules/actions app/modules/alerts tests/modules/test_actions_module.py tests/modules/test_alerts_module.py tests/integration/test_log_pipeline.py
git commit -m "feat: add actions api and alert placeholders"
```

### Task 7: Final Verification And Cleanup

**Files:**
- Modify: `tests/modules/test_health_module.py`
- Modify: `tests/modules/test_auth_module.py`
- Modify: `tests/core/test_registry.py`
- Modify: `Makefile` (only if a dedicated `test-integration` target is actually useful after running the suite)

- [ ] **Step 1: Write the failing verification expectations**

```python
def test_create_app_bootstraps_logsense_routes() -> None:
    from app.main import create_app

    routes = {route.path for route in create_app().routes}

    assert "/api/v1/logs" in routes
```

- [ ] **Step 2: Run the full suite to find breakages**

Run: `pytest -v`
Expected: FAIL only if older starter-kit tests still assume the obsolete module list or do not account for bootstrapped routes/tasks.

- [ ] **Step 3: Make the smallest compatibility edits**

```python
# tests/core/test_config.py
assert "app.modules.jobs.module" not in settings.enabled_modules
assert "app.modules.logs.module" in settings.enabled_modules
```

```python
# tests/core/test_registry.py
def test_bootstrap_celery_tasks_registers_module_tasks(monkeypatch) -> None:
    from celery import Celery

    from app.core.bootstrap import bootstrap_celery_tasks

    celery = Celery("test")
    module = DummyModule("health")
    monkeypatch.setattr(ModuleRegistry, "load_modules", lambda self: [module])

    tasks = bootstrap_celery_tasks(celery_app=celery, settings=Settings(auto_discover_modules=False))

    assert tasks == []
```

```python
# tests/modules/test_health_module.py
assert "/api/v1/logs" in {route.path for route in create_app(Settings()).routes}
```

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `pytest -v`
Expected: PASS with coverage still meeting the configured threshold.

- [ ] **Step 5: Commit**

```bash
git add tests/core/test_config.py tests/core/test_registry.py tests/modules/test_health_module.py tests/modules/test_auth_module.py Makefile
git commit -m "test: align starter coverage with logsense modules"
```

---

## Self-Review

### Spec Coverage

- Product overview and objectives: implemented by the full pipeline across Tasks 2-6.
- `POST /logs/ingest` and `GET /logs`: Task 2.
- Log processing, clustering, deduplication, spike detection, repeated failure detection: Task 3.
- AI root cause, severity, fix suggestion: Task 4.
- Incident model, lifecycle, and resolve endpoint: Task 5.
- Action model, action storage, and dashboard API: Task 6.
- Placeholder alert integrations only: Task 6.
- Async execution with Celery and BaseJob: Tasks 1, 3, 4, 5, 6.
- Error-safe persistence foundation and centralized metadata wiring: Task 1.
- Unit tests for clustering, anomaly detection, AI parsing: Tasks 3 and 4.
- Integration test for logs → analysis → AI → incident → action: Task 6.
- Out-of-scope frontend, streaming, advanced ML, and real alert delivery: intentionally not implemented.

### Placeholder Scan

- No `TODO`, `TBD`, or “implement later” placeholders remain in the task steps.
- The only intentional non-implementation is the alert placeholder module required by the PRD, and it is represented as explicit `NotImplementedError` interface stubs rather than vague notes.

### Type Consistency

- Message keys are consistent with the PRD: `logs.ingested`, `analysis.clustered`, `analysis.anomaly_detected`, `ai.analysis_completed`, `incident.created`, `incident.action_created`.
- Domain fields stay consistent across modules: `fingerprint`, `severity`, `root_cause`, `suggested_action`, `incident_id`, `status`.
- The pipeline payload shape is consistent: `logs` emits `fingerprint`, `analysis` emits `cluster`, `ai` emits structured analysis, `incident` emits `incident_id` for action creation.
