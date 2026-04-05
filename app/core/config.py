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
    enabled_modules: list[str] = Field(
        default_factory=lambda: [
            "app.modules.health.module",
            "app.modules.auth.module",
            "app.modules.email.module",
            "app.modules.jobs.module",
            "app.modules.system.module",
        ]
    )
    auto_discover_modules: bool = True
