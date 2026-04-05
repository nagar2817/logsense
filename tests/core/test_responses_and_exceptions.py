from starlette import status

from app.core import config
from app.core.exceptions.domain import ExternalServiceException
from app.core.exceptions.http import (
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException,
    ValidationException,
)
from app.core.messages.base import BaseMessageKeys
from app.core.messages.builder import build_message_key
from app.core.responses.base import success_response
from app.core.responses.errors import error_response


def test_success_response_contract() -> None:
    payload = success_response(
        message="Operation successful",
        message_key=build_message_key("jobs", "triggered"),
        data={"task_id": "abc"},
        meta={"request_id": "req-1"},
    )

    assert payload == {
        "success": True,
        "message": "Operation successful",
        "message_key": "jobs.triggered",
        "data": {"task_id": "abc"},
        "meta": {"request_id": "req-1"},
    }
    assert build_message_key("jobs", "triggered") == "jobs.triggered"


def test_error_response_contract() -> None:
    details = {"email_id": "missing"}
    exc = NotFoundException(
        message="Email not found",
        message_key="email.not_found",
        error_code="EMAIL_001",
        details=details,
    )

    assert error_response(exc) == {
        "success": False,
        "message": "Email not found",
        "message_key": "email.not_found",
        "error": {"code": "EMAIL_001", "details": {"email_id": "missing"}},
    }
    assert BaseMessageKeys.INTERNAL_ERROR == "system.internal_error"

    assert config.Settings.__name__ == "Settings"

    assert exc.details is details
    details["email_id"] = "updated"
    assert exc.details == {"email_id": "updated"}

    validation_exc = ValidationException(
        message="Invalid payload",
        error_code="VALIDATION_001",
    )
    assert validation_exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert validation_exc.message_key == BaseMessageKeys.VALIDATION_ERROR
    assert validation_exc.details == {}

    auth_exc = AuthenticationException()
    assert auth_exc.status_code == status.HTTP_401_UNAUTHORIZED
    assert auth_exc.message_key == BaseMessageKeys.UNAUTHORIZED

    authz_exc = AuthorizationException()
    assert authz_exc.status_code == status.HTTP_403_FORBIDDEN
    assert authz_exc.message_key == BaseMessageKeys.FORBIDDEN

    rate_limit_exc = RateLimitException()
    assert rate_limit_exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert rate_limit_exc.message_key == "auth.rate_limited"

    external_exc = ExternalServiceException(
        message="Service failed",
        message_key="external.failure",
        error_code="EXT_001",
    )
    assert external_exc.status_code == status.HTTP_502_BAD_GATEWAY
    assert external_exc.details == {}
