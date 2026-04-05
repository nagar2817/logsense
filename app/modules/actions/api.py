from fastapi import APIRouter

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.actions.messages import ActionMessageKeys
from app.modules.actions.schemas import ActionUpdateRequest
from app.modules.actions.services import ActionService

router = APIRouter(tags=["actions"])
settings = Settings()


def get_service() -> ActionService:
    return ActionService(settings=settings)


@router.get("/actions")
def list_actions() -> dict[str, object]:
    return success_response(
        message="Actions retrieved",
        message_key=ActionMessageKeys.LISTED,
        data=get_service().list_actions().model_dump(),
    )


@router.patch("/actions/{action_id}")
def update_action(action_id: str, payload: ActionUpdateRequest) -> dict[str, object]:
    return success_response(
        message="Action updated",
        message_key=ActionMessageKeys.UPDATED,
        data=get_service().update_status(action_id, payload.status).model_dump(),
    )
