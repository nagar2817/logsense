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

    def metrics_tags(self, payload: dict[str, Any]) -> dict[str, str]:
        return {"job": self.name, "idempotency_key": str(payload.get("idempotency_key", "missing"))}

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
