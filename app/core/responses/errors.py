"""Helpers for error response payloads."""

from typing import Any

from app.core.exceptions.base import BaseAppException


def error_response(exc: BaseAppException) -> dict[str, Any]:
    return {
        "success": False,
        "message": exc.message,
        "message_key": exc.message_key,
        "error": {
            "code": exc.error_code,
            "details": exc.details,
        },
    }
