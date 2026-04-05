import hashlib
import re

from app.core.config import Settings
from app.modules.logs.repository import LogRepository
from app.modules.logs.schemas import LogIngestRequest, LogListResponse, LogRecord


class LogService:
    def __init__(self, *, settings: Settings) -> None:
        self.repository = LogRepository(settings=settings)

    def build_fingerprint(self, *, service: str, level: str, message: str) -> str:
        normalized_message = re.sub(r"\d+", "<num>", message.lower()).strip()
        digest = hashlib.sha1(f"{service}:{level}:{normalized_message}".encode()).hexdigest()[:16]
        return f"{service}:{level}:{digest}"

    def ingest(self, payload: LogIngestRequest) -> LogRecord:
        return self.repository.create_log(
            service=payload.service,
            level=payload.level,
            message=payload.message,
            fingerprint=self.build_fingerprint(
                service=payload.service,
                level=payload.level,
                message=payload.message,
            ),
            timestamp=payload.timestamp.isoformat(),
        )

    def list_logs(self) -> LogListResponse:
        return LogListResponse(items=self.repository.list_logs(limit=100))
