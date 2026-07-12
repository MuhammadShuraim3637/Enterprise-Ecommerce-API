import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from app.core.config import settings


def generate_random_token() -> str:
    return secrets.token_urlsafe(32)


def create_jwt_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "exp": expire,
        "sub": str(subject),
        "type": token_type
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)