from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, service: AuthService = Depends(get_auth_service)):
    user = service.register(payload)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return service.login(payload)


@router.get("/verify-email")
def verify_email(token: str, service: AuthService = Depends(get_auth_service)):
    service.verify_email(token)
    return {"message": "Email verified successfully"}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, service: AuthService = Depends(get_auth_service)):
    service.forgot_password(payload.email)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, service: AuthService = Depends(get_auth_service)):
    service.reset_password(payload)
    return {"message": "Password reset successfully"}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str, service: AuthService = Depends(get_auth_service)):
    return service.refresh_access_token(refresh_token)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service = AuthService(UserRepository(db))
    service.logout(current_user)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/admin/verify-user/{user_id}")
def admin_verify_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_user)
):
    """Admin endpoint to manually verify a user - useful if email service fails"""
    if not current_admin.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_verified = True
    user.verification_token = None
    user_repo.save(user)
    
    return {"message": f"User {user.email} verified successfully"}