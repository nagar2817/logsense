import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions.base import BaseAppException
from app.core.messages.base import BaseMessageKeys
from app.core.responses.errors import error_response


def register_exception_handlers(app: FastAPI) -> None:
    logger = logging.getLogger("app.error")

    @app.exception_handler(BaseAppException)
    async def handle_known_exceptions(_: Request, exc: BaseAppException) -> JSONResponse:
        logger.warning("handled_app_exception", extra={"error_code": exc.error_code})
        return JSONResponse(status_code=exc.status_code, content=error_response(exc))

    @app.exception_handler(Exception)
    async def handle_unknown_exceptions(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
                "message_key": BaseMessageKeys.INTERNAL_ERROR,
                "error": {"code": "SYSTEM_001", "details": {}},
            },
        )
