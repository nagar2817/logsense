from app.core.config import Settings
from app.modules.actions.repository import ActionRepository
from app.modules.actions.schemas import ActionListResponse, ActionRecord


class ActionService:
    def __init__(self, *, settings: Settings) -> None:
        self.repository = ActionRepository(settings=settings)

    def create_action(self, *, incident_id: str, title: str, description: str) -> ActionRecord:
        return self.repository.create_action(
            incident_id=incident_id,
            title=title,
            description=description,
        )

    def list_actions(self) -> ActionListResponse:
        return ActionListResponse(items=self.repository.list_actions())

    def update_status(self, action_id: str, status: str) -> ActionRecord:
        return self.repository.update_status(action_id, status)
