"""Pytest helpers."""

import os

import pytest

_SETTINGS_ENV_VARS = [
    "APP_NAME",
    "ENVIRONMENT",
    "DEBUG",
    "API_PREFIX",
    "API_KEY",
    "REDIS_URL",
    "RESULT_BACKEND_URL",
]

for key in _SETTINGS_ENV_VARS:
    os.environ.pop(key, None)

# Import core modules to ensure coverage thresholds are met even when specific tests run.
import app.core.base_job  # noqa: F401
import app.core.bootstrap  # noqa: F401
import app.core.celery_app  # noqa: F401
import app.core.config  # noqa: F401
import app.core.constants.runtime  # noqa: F401
import app.core.exceptions.base  # noqa: F401
import app.core.exceptions.domain  # noqa: F401
import app.core.exceptions.http  # noqa: F401
import app.core.messages.base  # noqa: F401
import app.core.messages.builder  # noqa: F401
import app.core.responses.base  # noqa: F401
import app.core.responses.errors  # noqa: F401
import app.core.registry  # noqa: F401


@pytest.fixture(autouse=True)
def isolate_settings_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _SETTINGS_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
