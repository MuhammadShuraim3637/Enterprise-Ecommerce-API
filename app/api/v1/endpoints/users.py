from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user, get_admin_user
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Logged-in user apni profile dekh sake (Jo Postman pe check nahi ho raha tha, ab yahan secure chalega)
    """
    return current_user

@router.put("/me/update", response_model=UserResponse)
def update_user_me(
    obj_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Logged-in user apni details khud update kare
    """
    service = UserService(db)
    updated_user = service.update_user_profile(current_user, obj_in)
    return updated_user

@router.get("/", response_model=List[UserResponse])
def read_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)  # Sirf admin access kar sake
):
    """
    Get all users (Admin Only)
    """
    service = UserService(db)
    return service.get_all_users(skip=skip, limit=limit)