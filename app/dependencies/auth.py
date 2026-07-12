from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

# Swagger/Postman headers se token read karne ke liye setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Token decode aur validation
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # Check karna ke token access token hi hai ya nahi
        if email is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    
    if user is None:
        raise credentials_exception
        
    # Check: Kya user ka account active hai?
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user account"
        )

    # NOTE: email verification is intentionally NOT enforced here.
    # This is a portfolio/demo project — accounts can log in and use the API
    # immediately after registering, without clicking a verification link.
    # The verification flow (register → token → /auth/verify-email) still
    # exists in the codebase and works end-to-end; it's just not required
    # to access protected routes. Admin promotion is done manually via a
    # direct SQL UPDATE on the database (see README).

    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough privileges"
        )
    return current_user