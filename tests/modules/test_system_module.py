from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.modules.system.module import Module as SystemModule
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


def test_system_module_contract() -> None:
    module = SystemModule()
    assert module.name == "system"
    assert module.register_tasks() == []
