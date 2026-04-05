from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings
from app.core.constants.runtime import API_KEY_HEADER, HEALTH_ENDPOINTS
from app.core.exceptions.http import AuthenticationException
from app.core.responses.errors import error_response
from app.modules.auth.services import AuthService


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object, *, settings: Settings) -> None:
        super().__init__(app)
        self.auth_service = AuthService(settings=settings)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path.endswith(tuple(HEALTH_ENDPOINTS)):
            return await call_next(request)
        if not self.auth_service.is_valid_api_key(request.headers.get(API_KEY_HEADER)):
            exc = AuthenticationException(message="Invalid API key")
            return JSONResponse(status_code=exc.status_code, content=error_response(exc))
        return await call_next(request)
