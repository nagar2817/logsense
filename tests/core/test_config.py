import os

_MUTABLE_ENV = [
    "APP_NAME",
    "ENVIRONMENT",
    "DEBUG",
    "API_PREFIX",
    "API_KEY",
    "REDIS_URL",
    "RESULT_BACKEND_URL",
    "SQLITE_DATABASE_PATH",
    "ANALYSIS_WINDOW_MINUTES",
    "ERROR_FREQUENCY_THRESHOLD",
    "SPIKE_MULTIPLIER",
    "LLM_ENABLED",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_TIMEOUT_SECONDS",
]

for key in _MUTABLE_ENV:
    os.environ.pop(key, None)

from app.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "pipeline-execution"
    assert settings.api_prefix == "/api/v1"
    assert settings.sqlite_database_path == "data/logsense.db"
    assert settings.analysis_window_minutes == 15
    assert settings.error_frequency_threshold == 5
    assert settings.spike_multiplier == 2.0
    assert settings.enabled_modules == [
        "app.modules.health.module",
        "app.modules.auth.module",
        "app.modules.email.module",
        "app.modules.system.module",
    ]
    assert settings.environment == "local"
    assert settings.debug is False
    assert settings.api_key == "local-dev-key"
    assert settings.redis_url == "redis://redis:6379/0"
    assert settings.result_backend_url == "redis://redis:6379/1"
    assert settings.llm_enabled is False
    assert settings.llm_base_url == "https://api.openai.com/v1"
    assert settings.llm_api_key == ""
    assert settings.llm_model == "gpt-4.1-mini"
    assert settings.llm_timeout_seconds == 20
    assert settings.auto_discover_modules is True

    # Each instantiation should produce a fresh enabled_modules list
    another_settings = Settings()
    assert settings.enabled_modules is not another_settings.enabled_modules
