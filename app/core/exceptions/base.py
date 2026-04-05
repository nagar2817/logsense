"""Base exception contract used by HTTP and domain errors."""


class BaseAppException(Exception):
    def __init__(
        self,
        *,
        message: str,
        message_key: str,
        error_code: str,
        status_code: int,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.message_key = message_key
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
