from typing import Literal

from pydantic import BaseModel


class ActionRecord(BaseModel):
    id: str
    incident_id: str
    title: str
    description: str
    status: Literal["open", "completed"]
    created_at: str
    updated_at: str


class ActionListResponse(BaseModel):
    items: list[ActionRecord]


class ActionUpdateRequest(BaseModel):
    status: Literal["open", "completed"]
