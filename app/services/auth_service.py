from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from app.core.security import get_password_hash, verify_password
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, ResetPasswordRequest
from app.schemas.user import UserCreate
from app.services.email_service import EmailService
from app.utils.token import generate_random_token, create_jwt_token


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(self, schema_in: UserCreate) -> User:
        if self.user_repo.get_by_email(schema_in.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_pass = get_password_hash(schema_in.password)
        verify_token = generate_random_token()
        user = self.user_repo.create(schema_in, hashed_pass, verify_token)
        
        EmailService.send_verification_email(user.email, verify_token)
        return user

    def login(self, schema_in: LoginRequest) -> dict:
        user = self.user_repo.get_by_email(schema_in.email)
        if not user or not verify_password(schema_in.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is disabled")

        access_token = create_jwt_token(
            user.email, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access"
        )
        refresh_token = create_jwt_token(
            user.email, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS), "refresh"
        )
        
        user.refresh_token = refresh_token
        self.user_repo.save(user)
        
        return {"access_token": access_token, "refresh_token": refresh_token}

    def verify_email(self, token: str) -> bool:
        user = self.user_repo.get_by_verification_token(token)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        user.is_verified = True
        user.verification_token = None
        self.user_repo.save(user)
        return True

    def forgot_password(self, email: str):
        user = self.user_repo.get_by_email(email)
        if user:
            reset_token = generate_random_token()
            user.password_reset_token = reset_token
            self.user_repo.save(user)
            EmailService.send_password_reset_email(user.email, reset_token)

    def reset_password(self, schema_in: ResetPasswordRequest):
        user = self.user_repo.get_by_reset_token(schema_in.token)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        user.hashed_password = get_password_hash(schema_in.new_password)
        user.password_reset_token = None
        self.user_repo.save(user)

    def refresh_access_token(self, refresh_token: str) -> dict:
        user = self.user_repo.get_by_refresh_token(refresh_token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        access_token = create_jwt_token(
            user.email, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), "access"
        )
        return {"access_token": access_token, "refresh_token": refresh_token}

    def logout(self, user: User):
        user.refresh_token = None
        self.user_repo.save(user)