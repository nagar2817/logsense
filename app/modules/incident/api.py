from fastapi import APIRouter

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.incident.messages import IncidentMessageKeys
from app.modules.incident.services import IncidentService

router = APIRouter(tags=["incident"])
settings = Settings()


def get_service() -> IncidentService:
    return IncidentService(settings=settings)


@router.get("/incidents")
def list_incidents() -> dict[str, object]:
    return success_response(
        message="Incidents retrieved",
        message_key=IncidentMessageKeys.LISTED,
        data=get_service().list_incidents().model_dump(),
    )


@router.get("/incidents/{incident_id}")
def incident_detail(incident_id: str) -> dict[str, object]:
    return success_response(
        message="Incident detail retrieved",
        message_key=IncidentMessageKeys.DETAIL,
        data=get_service().get_incident_detail(incident_id).model_dump(),
    )


@router.patch("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str) -> dict[str, object]:
    return success_response(
        message="Incident resolved",
        message_key=IncidentMessageKeys.RESOLVED,
        data=get_service().resolve_incident(incident_id).model_dump(),
    )
