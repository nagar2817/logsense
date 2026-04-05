from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_connection
from app.modules.actions.schemas import ActionRecord


class ActionRepository:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def create_action(self, *, incident_id: str, title: str, description: str) -> ActionRecord:
        now = datetime.now(UTC).isoformat()
        action = ActionRecord(
            id=f"ACT-{uuid4().hex[:8].upper()}",
            incident_id=incident_id,
            title=title,
            description=description,
            status="open",
            created_at=now,
            updated_at=now,
        )
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                INSERT INTO actions (id, incident_id, title, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    action.id,
                    action.incident_id,
                    action.title,
                    action.description,
                    action.status,
                    action.created_at,
                    action.updated_at,
                ),
            )
        return action

    def list_actions(self) -> list[ActionRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, incident_id, title, description, status, created_at, updated_at
                FROM actions
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [ActionRecord.model_validate(dict(row)) for row in rows]

    def update_status(self, action_id: str, status: str) -> ActionRecord:
        now = datetime.now(UTC).isoformat()
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                UPDATE actions
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, action_id),
            )
            row = connection.execute(
                """
                SELECT id, incident_id, title, description, status, created_at, updated_at
                FROM actions
                WHERE id = ?
                """,
                (action_id,),
            ).fetchone()
        return ActionRecord.model_validate(dict(row))
