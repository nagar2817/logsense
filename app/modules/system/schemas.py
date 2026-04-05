from pydantic import BaseModel


class SystemInfo(BaseModel):
    app_name: str
    environment: str


class MetricsState(BaseModel):
    metrics_enabled: bool
