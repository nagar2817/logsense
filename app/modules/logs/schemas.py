from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class LogIngestRequest(BaseModel):
    service: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    message: str
    timestamp: datetime


class LogRecord(BaseModel):
    id: str
    service: str
    level: str
    message: str
    fingerprint: str
    timestamp: str
    created_at: str


class LogListResponse(BaseModel):
    items: list[LogRecord]
