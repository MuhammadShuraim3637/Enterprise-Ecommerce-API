from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate
from app.core.security import get_password_hash

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.repo.get_by_id(user_id)  # Ya jo bhi aapki repo mein method name hai

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        # Agar repo mein query method standard hai:
        return self.repo.db.query(User).offset(skip).limit(limit).all()

    def update_user_profile(self, user: User, obj_in: UserUpdate) -> User:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Agar password bhi update ho raha hai to use hash karo
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
            
        for field in update_data:
            if hasattr(user, field):
                setattr(user, field, update_data[field])
                
        self.repo.db.commit()
        self.repo.db.refresh(user)
        return user