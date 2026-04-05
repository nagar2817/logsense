from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.actions.services import ActionService
from app.modules.logs.api import router as logs_router


def test_full_log_pipeline_creates_incident_and_action(monkeypatch, tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        error_frequency_threshold=1,
        llm_enabled=False,
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)

    monkeypatch.setattr("app.modules.logs.api.settings", settings)
    monkeypatch.setattr("app.modules.analysis.jobs.settings", settings)
    monkeypatch.setattr("app.modules.ai.jobs.settings", settings)
    monkeypatch.setattr("app.modules.incident.jobs.settings", settings)
    monkeypatch.setattr("app.modules.actions.jobs.settings", settings)

    monkeypatch.setattr(
        "app.modules.logs.jobs.start_log_pipeline_job.delay",
        lambda payload: (
            __import__("app.modules.logs.jobs", fromlist=["start_log_pipeline_job"]).job.execute(payload),
            type("Result", (), {"id": "job-inline"})(),
        )[1],
    )
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
