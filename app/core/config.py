from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "pipeline-execution"
    environment: str = "local"
    debug: bool = False
    api_prefix: str = "/api/v1"
    api_key: str = "local-dev-key"
    redis_url: str = "redis://redis:6379/0"
    result_backend_url: str = "redis://redis:6379/1"
    sqlite_database_path: str = "data/logsense.db"
    analysis_window_minutes: int = 15
    error_frequency_threshold: int = 5
    spike_multiplier: float = 2.0
    llm_enabled: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 20
    enabled_modules: list[str] = Field(
        default_factory=lambda: [
            "app.modules.health.module",
            "app.modules.auth.module",
            "app.modules.email.module",
            "app.modules.system.module",
            "app.modules.logs.module",
            "app.modules.analysis.module",
            "app.modules.ai.module",
            "app.modules.incident.module",
            "app.modules.actions.module",
            "app.modules.alerts.module",
        ]
    )
    auto_discover_modules: bool = True
