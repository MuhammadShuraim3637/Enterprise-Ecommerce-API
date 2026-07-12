import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category_schema import CategoryCreate, CategoryUpdate

class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_slug(self, name: str) -> str:
        # Lowercase karke saare special characters ko hyphen (-) se replace karna
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.query(Category).filter(Category.id == category_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Category]:
        return self.db.query(Category).offset(skip).limit(limit).all()

    def create(self, obj_in: CategoryCreate) -> Category:
        slug = self._generate_slug(obj_in.name)
        db_obj = Category(
            name=obj_in.name,
            slug=slug,
            description=obj_in.description
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, category_id: int, obj_in: CategoryUpdate) -> Optional[Category]:
        db_obj = self.get_by_id(category_id)
        if not db_obj:
            return None
            
        update_data = obj_in.model_dump(exclude_unset=True)
        if "name" in update_data:
            update_data["slug"] = self._generate_slug(update_data["name"])
            
        for field in update_data:
            setattr(db_obj, field, update_data[field])
            
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj