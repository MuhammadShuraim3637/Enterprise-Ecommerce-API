from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_verification_token(self, token: str) -> Optional[User]:
        return self.db.query(User).filter(User.verification_token == token).first()

    def get_by_reset_token(self, token: str) -> Optional[User]:
        return self.db.query(User).filter(User.password_reset_token == token).first()

    def get_by_refresh_token(self, token: str) -> Optional[User]:
        return self.db.query(User).filter(User.refresh_token == token).first()

    def create(self, schema_in: UserCreate, hashed_pass: str, verification_token: str) -> User:
        user = User(
            email=schema_in.email,
            hashed_password=hashed_pass,
            full_name=schema_in.full_name,
            verification_token=verification_token
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, schema_in: UserUpdate) -> User:
        update_data = schema_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user