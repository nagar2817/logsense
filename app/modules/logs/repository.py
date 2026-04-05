from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.core.database import get_connection
from app.modules.logs.schemas import LogRecord


class LogRepository:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def create_log(
        self,
        *,
        service: str,
        level: str,
        message: str,
        fingerprint: str,
        timestamp: str,
    ) -> LogRecord:
        record = LogRecord(
            id=f"LOG-{uuid4().hex[:12]}",
            service=service,
            level=level,
            message=message,
            fingerprint=fingerprint,
            timestamp=timestamp,
            created_at=datetime.now(UTC).isoformat(),
        )
        with get_connection(settings=self.settings) as connection:
            connection.execute(
                """
                INSERT INTO logs (id, service, level, message, fingerprint, timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.service,
                    record.level,
                    record.message,
                    record.fingerprint,
                    record.timestamp,
                    record.created_at,
                ),
            )
        return record

    def list_logs(self, *, limit: int) -> list[LogRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, service, level, message, fingerprint, timestamp, created_at
                FROM logs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [LogRecord.model_validate(dict(row)) for row in rows]

    def list_by_fingerprint(self, *, fingerprint: str, limit: int) -> list[LogRecord]:
        with get_connection(settings=self.settings) as connection:
            rows = connection.execute(
                """
                SELECT id, service, level, message, fingerprint, timestamp, created_at
                FROM logs
                WHERE fingerprint = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (fingerprint, limit),
            ).fetchall()
        return [LogRecord.model_validate(dict(row)) for row in rows]
