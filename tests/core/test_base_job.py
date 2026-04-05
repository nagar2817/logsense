import logging

from celery import Celery
import pytest

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.exceptions.domain import ExternalServiceException
from app.core.logging import configure_logging
from app.core.messages.builder import build_message_key
from app.core.responses.base import success_response
from app.core.responses.errors import error_response
from app.utils.context import clear_request_context, get_request_context, set_request_context


class DummyJob(BaseJob):
    name = "dummy.job"

    def run(self, payload: dict[str, str]) -> dict[str, str]:
        return {"status": payload["status"]}


def test_base_job_execute_wraps_payload() -> None:
    result = DummyJob(celery_app=Celery("test")).execute({"status": "ok"})
    assert result == {"status": "ok"}


class FailingJob(BaseJob):
    name = "failing.job"

    def run(self, payload: dict[str, str]) -> dict[str, str]:
        raise RuntimeError(payload["status"])


def test_base_job_execute_raises_after_failure() -> None:
    with pytest.raises(RuntimeError, match="boom"):
        FailingJob(celery_app=Celery("test")).execute({"status": "boom"})


def test_celery_app_configuration() -> None:
    assert celery_app.conf.task_default_queue == "default"
    assert celery_app.conf.task_track_started is True


def test_context_logging_and_contract_helpers() -> None:
    set_request_context(request_id="req-1", correlation_id="corr-1")
    assert get_request_context() == {"request_id": "req-1", "correlation_id": "corr-1"}
    clear_request_context()
    assert get_request_context() == {"request_id": None, "correlation_id": None}

    configure_logging()
    assert logging.getLogger().handlers[0].formatter is not None

    payload = success_response(
        message="ok",
        message_key=build_message_key("jobs", "triggered"),
    )
    assert payload["message_key"] == "jobs.triggered"
    assert payload["data"] == {}
    assert payload["meta"] == {}

    exc = ExternalServiceException(
        message="Service failed",
        message_key="system.external_failure",
        error_code="SYSTEM_999",
    )
    assert error_response(exc)["error"]["code"] == "SYSTEM_999"
