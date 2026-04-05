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


def test_incident_api_returns_detail_with_related_logs(monkeypatch, tmp_path) -> None:
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

    monkeypatch.setattr("app.modules.incident.api.settings", settings)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get(f"/api/v1/incidents/{incident.id}")

    assert response.status_code == 200
    assert response.json()["message_key"] == "incident.detail"
    assert response.json()["data"]["logs"][0]["service"] == "payment"
