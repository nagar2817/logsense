from pydantic import BaseModel


class AuthValidationResult(BaseModel):
    authenticated: bool
    scheme: str
