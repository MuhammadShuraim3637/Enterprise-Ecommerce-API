from typing import Any, List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # so leftover SMTP_* vars in Railway don't break startup
    )

    # App
    APP_NAME: str = "Enterprise Ecommerce API"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str

    # Email (Resend — HTTP API, works from platforms like Railway that block
    # outbound SMTP ports). Get RESEND_API_KEY from https://resend.com/api-keys
    RESEND_API_KEY: str
    EMAIL_FROM: str = "onboarding@resend.dev"

    # Old SMTP settings kept as optional so leftover Railway env vars don't
    # cause a validation error — they are no longer used.
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024

    ALLOWED_IMAGE_TYPES: Any = [
        "jpg",
        "jpeg",
        "png",
        "webp",
    ]

    @field_validator("ALLOWED_IMAGE_TYPES", mode="before")
    @classmethod
    def assemble_image_types(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


settings = Settings()
