import os

_MUTABLE_ENV = [
    "APP_NAME",
    "ENVIRONMENT",
    "DEBUG",
    "API_PREFIX",
    "API_KEY",
    "REDIS_URL",
    "RESULT_BACKEND_URL",
]

for key in _MUTABLE_ENV:
    os.environ.pop(key, None)

from app.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "pipeline-execution"
    assert settings.api_prefix == "/api/v1"
    assert settings.enabled_modules == [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.jobs.module",
        "app.modules.system.module",
    ]
    assert settings.environment == "local"
    assert settings.debug is False
    assert settings.api_key == "local-dev-key"
    assert settings.redis_url == "redis://redis:6379/0"
    assert settings.result_backend_url == "redis://redis:6379/1"
    assert settings.auto_discover_modules is True

    # Each instantiation should produce a fresh enabled_modules list
    another_settings = Settings()
    assert settings.enabled_modules is not another_settings.enabled_modules
