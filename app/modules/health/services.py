from app.modules.health.schemas import HealthState


class HealthService:
    def health(self) -> HealthState:
        return HealthState(status="ok", redis="unknown")

    def ready(self) -> HealthState:
        return HealthState(status="ready", redis="up")
