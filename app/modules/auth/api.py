from fastapi import APIRouter

from app.core.responses.base import success_response
from app.modules.auth.messages import AuthMessageKeys
from app.modules.auth.schemas import AuthValidationResult

router = APIRouter(tags=["auth"])


@router.get("/auth/validate")
def validate_auth() -> dict[str, object]:
    return success_response(
        message="API key valid",
        message_key=AuthMessageKeys.VALID,
        data=AuthValidationResult(authenticated=True, scheme="api_key").model_dump(),
    )
