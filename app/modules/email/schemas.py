from pydantic import BaseModel, EmailStr


class EmailPayload(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    idempotency_key: str


class EmailReceipt(BaseModel):
    status: str
    recipient: EmailStr
    idempotency_key: str
