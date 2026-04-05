from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_request_context(*, request_id: str | None, correlation_id: str | None) -> None:
    _request_id.set(request_id)
    _correlation_id.set(correlation_id)


def get_request_context() -> dict[str, str | None]:
    return {
        "request_id": _request_id.get(),
        "correlation_id": _correlation_id.get(),
    }


def clear_request_context() -> None:
    set_request_context(request_id=None, correlation_id=None)
