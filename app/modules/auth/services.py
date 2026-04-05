from app.core.config import Settings


class AuthService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings

    def is_valid_api_key(self, api_key: str | None) -> bool:
        return api_key == self.settings.api_key
