from fastapi import APIRouter, status

from app.core.responses.base import success_response
from app.modules.email.jobs import send_email_job
from app.modules.email.messages import EmailMessageKeys
from app.modules.email.schemas import EmailPayload

router = APIRouter(tags=["email"])


@router.post("/email/send", status_code=status.HTTP_202_ACCEPTED)
def trigger_email(payload: EmailPayload) -> dict[str, object]:
    async_result = send_email_job.delay(payload.model_dump())
    return success_response(
        message="Email job queued",
        message_key=EmailMessageKeys.EMAIL_QUEUED,
        data={"task_id": async_result.id},
    )
