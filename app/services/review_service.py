from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.review import Review
from app.schemas.review_schema import ReviewCreate, ReviewUpdate

class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, review_id: int) -> Optional[Review]:
        return self.db.query(Review).filter(Review.id == review_id).first()

    def get_by_product(self, product_id: int, skip: int = 0, limit: int = 50) -> List[Review]:
        return self.db.query(Review).filter(Review.product_id == product_id).offset(skip).limit(limit).all()

    def create(self, obj_in: ReviewCreate, user_id: int) -> Review:
        db_obj = Review(
            product_id=obj_in.product_id,
            user_id=user_id,
            rating=obj_in.rating,
            comment=obj_in.comment
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, review_id: int) -> bool:
        db_obj = self.get_by_id(review_id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True