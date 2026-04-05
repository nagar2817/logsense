from fastapi import FastAPI

from app.core.config import Settings
from app.core.logging import configure_logging
from app.core.middleware.auth import AuthMiddleware
from app.core.middleware.error_handler import register_exception_handlers
from app.core.middleware.logging import LoggingMiddleware
from app.core.middleware.request_id import RequestIDMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    configure_logging()
    app = FastAPI(title=resolved_settings.app_name, debug=resolved_settings.debug)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(AuthMiddleware, settings=resolved_settings)
    register_exception_handlers(app)
    return app


app = create_app()
