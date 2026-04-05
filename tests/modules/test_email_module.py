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
