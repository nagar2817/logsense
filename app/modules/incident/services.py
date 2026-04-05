from app.core.config import Settings
from app.modules.incident.repository import IncidentRepository
from app.modules.incident.schemas import IncidentDetail, IncidentListResponse, IncidentRecord
from app.modules.logs.repository import LogRepository


class IncidentService:
    def __init__(self, *, settings: Settings) -> None:
        self.repository = IncidentRepository(settings=settings)
        self.log_repository = LogRepository(settings=settings)

    def create_incident(
        self,
        *,
        fingerprint: str,
        title: str,
        severity: str,
        root_cause: str,
        suggested_action: str,
    ) -> IncidentRecord:
        return self.repository.create_incident(
            fingerprint=fingerprint,
            title=title,
            severity=severity,
            root_cause=root_cause,
            suggested_action=suggested_action,
        )

    def list_incidents(self) -> IncidentListResponse:
        return IncidentListResponse(items=self.repository.list_incidents())

    def get_incident_detail(self, incident_id: str) -> IncidentDetail:
        incident = self.repository.get_incident(incident_id)
        return IncidentDetail(
            incident=incident,
            logs=self.log_repository.list_by_fingerprint(fingerprint=incident.fingerprint, limit=50),
        )

    def resolve_incident(self, incident_id: str) -> IncidentRecord:
        return self.repository.resolve_incident(incident_id)
