"""Test helpers for pipeline execution."""

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


@pytest.fixture(autouse=True)
def isolate_settings_env(monkeypatch):
    """Remove any ambient settings variables so tests stay deterministic."""
    for key in _SETTINGS_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
