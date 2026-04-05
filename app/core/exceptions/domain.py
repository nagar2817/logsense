"""Domain-specific exceptions raised from downstream services."""

from starlette import status

from app.core.exceptions.base import BaseAppException


class ExternalServiceException(BaseAppException):
    def __init__(
        self,
        *,
        message: str,
        message_key: str,
        error_code: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            message_key=message_key,
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )
