"""HTTP-specific application exceptions."""

from starlette import status

from app.core.exceptions.base import BaseAppException
from app.core.messages.base import BaseMessageKeys


class ValidationException(BaseAppException):
    def __init__(self, *, message: str, error_code: str, details: dict[str, object] | None = None) -> None:
        super().__init__(
            message=message,
            message_key=BaseMessageKeys.VALIDATION_ERROR,
            error_code=error_code,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )


class AuthenticationException(BaseAppException):
    def __init__(self, *, message: str = "Unauthorized", error_code: str = "AUTH_001") -> None:
        super().__init__(
            message=message,
            message_key=BaseMessageKeys.UNAUTHORIZED,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationException(BaseAppException):
    def __init__(self, *, message: str = "Forbidden", error_code: str = "AUTH_002") -> None:
        super().__init__(
            message=message,
            message_key=BaseMessageKeys.FORBIDDEN,
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(BaseAppException):
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
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class RateLimitException(BaseAppException):
    def __init__(self, *, message: str = "Rate limit exceeded", error_code: str = "AUTH_003") -> None:
        super().__init__(
            message=message,
            message_key="auth.rate_limited",
            error_code=error_code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )
