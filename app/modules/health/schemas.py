from pydantic import BaseModel


class HealthState(BaseModel):
    status: str
    redis: str
