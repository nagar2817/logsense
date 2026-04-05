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

    monkeypatch.setattr("app.modules.logs.api.settings", settings)

    def fake_delay(payload: dict[str, object]) -> object:
        queued["payload"] = payload
        return type("Result", (), {"id": "job-1"})()

    monkeypatch.setattr(
        start_log_pipeline_job,
        "delay",
        fake_delay,
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


def test_get_logs_returns_recent_records(monkeypatch, tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    repo = LogRepository(settings=settings)
    repo.create_log(
        service="payment",
        level="ERROR",
        message="Redis timeout",
        fingerprint="payment:error:redis-timeout",
        timestamp="2026-04-05T10:00:00Z",
    )

    monkeypatch.setattr("app.modules.logs.api.settings", settings)
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    response = TestClient(app).get("/api/v1/logs")

    assert response.status_code == 200
    assert response.json()["data"]["items"][0]["service"] == "payment"
