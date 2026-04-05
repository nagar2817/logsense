from app.modules.email.schemas import EmailPayload, EmailReceipt


class EmailService:
    def send_email(self, payload: dict[str, str]) -> dict[str, str]:
        parsed = EmailPayload.model_validate(payload)
        return EmailReceipt(
            status="queued_for_delivery",
            recipient=parsed.to_email,
            idempotency_key=parsed.idempotency_key,
        ).model_dump()
