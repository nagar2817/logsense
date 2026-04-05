from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.actions.api import router as actions_router
from app.modules.actions.services import ActionService


def test_action_api_lists_and_updates_status(monkeypatch, tmp_path) -> None:
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

    monkeypatch.setattr("app.modules.actions.api.settings", settings)
    app = FastAPI()
    app.include_router(actions_router, prefix="/api/v1")
    client = TestClient(app)

    listed = client.get("/api/v1/actions")
    updated = client.patch(f"/api/v1/actions/{action.id}", json={"status": "completed"})

    assert listed.status_code == 200
    assert listed.json()["data"]["items"][0]["title"] == "Increase Redis pool size"
    assert updated.json()["data"]["status"] == "completed"
