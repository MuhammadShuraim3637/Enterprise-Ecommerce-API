import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.product import Product, ProductImage
from app.schemas.product_schema import ProductCreate, ProductUpdate

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def _generate_slug(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        return self.db.query(Product).offset(skip).limit(limit).all()

    def get_products_advanced(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: Optional[str] = "id",
        sort_order: Optional[str] = "desc",
        page: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Advanced dynamic querying supporting Search, Filter, Sort and Pagination.
        """
        query = self.db.query(Product)

        # 1. Advanced Text Search
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%") | Product.description.ilike(f"%{search}%"))

        # 2. Filtering
        if category_id:
            query = query.filter(Product.category_id == category_id)
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # 3. Dynamic Sorting safely
        sort_attr = getattr(Product, sort_by if hasattr(Product, sort_by) else "id")
        if sort_order.lower() == "desc":
            query = query.order_by(sort_attr.desc())
        else:
            query = query.order_by(sort_attr.asc())

        # 4. Pagination
        total_items = query.count()
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()

        return {
            "items": items,
            "total_items": total_items,
            "page": page,
            "limit": limit,
            "total_pages": (total_items + limit - 1) // limit
        }

    def create(self, obj_in: ProductCreate) -> Product:
        slug = self._generate_slug(obj_in.name)
        db_obj = Product(
            category_id=obj_in.category_id,
            name=obj_in.name,
            slug=slug,
            description=obj_in.description,
            price=obj_in.price,
            stock=obj_in.stock
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, product_id: int, obj_in: ProductUpdate) -> Optional[Product]:
        db_obj = self.get_by_id(product_id)
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

    def add_image(self, product_id: int, image_url: str, is_primary: bool = False) -> ProductImage:
        db_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            is_primary=is_primary
        )
        self.db.add(db_image)
        self.db.commit()
        self.db.refresh(db_image)
        return db_image

    def delete_image(self, image_id: int) -> bool:
        db_image = self.db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if not db_image:
            return False
        self.db.delete(db_image)
        self.db.commit()
        return True

    def set_primary_image(self, product_id: int, image_id: int) -> Optional[ProductImage]:
        # Remove primary from all images of this product
        self.db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_primary == True
        ).update({ProductImage.is_primary: False})
        
        # Set new primary
        db_image = self.db.query(ProductImage).filter(ProductImage.id == image_id).first()
        if db_image:
            db_image.is_primary = True
            self.db.commit()
            self.db.refresh(db_image)
        return db_image