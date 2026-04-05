"""Helpers for response payloads."""

from typing import Any


def success_response(
    *,
    message: str,
    message_key: str,
    data: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "message_key": message_key,
        "data": data or {},
        "meta": meta or {},
    }
