from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_connection
from app.modules.incident.schemas import IncidentRecord


class IncidentRepository:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def create_incident(
        self,
        *,
        fingerprint: str,
        title: str,
        severity: str,
        root_cause: str,
        suggested_action: str,
    ) -> IncidentRecord:
        now = datetime.now(UTC).isoformat()
        incident = IncidentRecord(
            id=f"INC-{uuid4().hex[:8].upper()}",
            fingerprint=fingerprint,
            title=title,
            severity=severity,
            status="open",
            root_cause=root_cause,
            suggested_action=suggested_action,
            created_at=now,
            updated_at=now,
            resolved_at=None,
        )
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                INSERT INTO incidents (
                    id, fingerprint, title, severity, status, root_cause,
                    suggested_action, created_at, updated_at, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident.id,
                    incident.fingerprint,
                    incident.title,
                    incident.severity,
                    incident.status,
                    incident.root_cause,
                    incident.suggested_action,
                    incident.created_at,
                    incident.updated_at,
                    incident.resolved_at,
                ),
            )
        return incident

    def list_incidents(self) -> list[IncidentRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, fingerprint, title, severity, status, root_cause,
                       suggested_action, created_at, updated_at, resolved_at
                FROM incidents
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [IncidentRecord.model_validate(dict(row)) for row in rows]

    def get_incident(self, incident_id: str) -> IncidentRecord:
        with get_connection(settings=self.settings) as connection:
            row = connection.execute(
                """
                SELECT id, fingerprint, title, severity, status, root_cause,
                       suggested_action, created_at, updated_at, resolved_at
                FROM incidents
                WHERE id = ?
                """,
                (incident_id,),
            ).fetchone()
        return IncidentRecord.model_validate(dict(row))

    def resolve_incident(self, incident_id: str) -> IncidentRecord:
        now = datetime.now(UTC).isoformat()
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                UPDATE incidents
                SET status = 'resolved', updated_at = ?, resolved_at = ?
                WHERE id = ?
                """,
                (now, now, incident_id),
            )
        return self.get_incident(incident_id)
