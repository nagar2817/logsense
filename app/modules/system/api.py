from fastapi import APIRouter

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.system.messages import SystemMessageKeys
from app.modules.system.services import SystemService

router = APIRouter(tags=["system"])
service = SystemService(settings=Settings())


@router.get("/system/info")
def system_info() -> dict[str, object]:
    return success_response(
        message="System info retrieved",
        message_key=SystemMessageKeys.INFO,
        data=service.info().model_dump(),
    )


@router.get("/system/metrics")
def system_metrics() -> dict[str, object]:
    return success_response(
        message="Metrics placeholder",
        message_key=SystemMessageKeys.METRICS,
        data=service.metrics().model_dump(),
    )
