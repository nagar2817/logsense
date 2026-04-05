from pydantic import BaseModel

from app.modules.logs.schemas import LogRecord


class IncidentRecord(BaseModel):
    id: str
    fingerprint: str
    title: str
    severity: str
    status: str
    root_cause: str
    suggested_action: str
    created_at: str
    updated_at: str
    resolved_at: str | None = None


class IncidentListResponse(BaseModel):
    items: list[IncidentRecord]


class IncidentDetail(BaseModel):
    incident: IncidentRecord
    logs: list[LogRecord]
