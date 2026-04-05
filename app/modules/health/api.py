from fastapi import APIRouter

from app.core.responses.base import success_response
from app.modules.health.messages import HealthMessageKeys
from app.modules.health.services import HealthService

router = APIRouter(tags=["health"])
service = HealthService()


@router.get("/health")
def health() -> dict[str, object]:
    return success_response(
        message="Service is healthy",
        message_key=HealthMessageKeys.OK,
        data=service.health().model_dump(),
    )


@router.get("/ready")
def ready() -> dict[str, object]:
    return success_response(
        message="Service is ready",
        message_key=HealthMessageKeys.READY,
        data=service.ready().model_dump(),
    )
