from app.core.config import Settings
from app.modules.system.schemas import MetricsState, SystemInfo


class SystemService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def info(self) -> SystemInfo:
        return SystemInfo(app_name=self.settings.app_name, environment=self.settings.environment)

    def metrics(self) -> MetricsState:
        return MetricsState(metrics_enabled=False)
