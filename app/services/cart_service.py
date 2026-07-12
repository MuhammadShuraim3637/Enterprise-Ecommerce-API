from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.cart import CartItem
from app.models.product import Product
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate

class CartService:
    
    @staticmethod
    def get_user_cart(db: Session, user_id: int):
        items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
        
        # Total price aur item count calculate kar rahe hain
        total_items = sum(item.quantity for item in items)
        total_price = sum(float(item.product.price) * item.quantity for item in items if item.product)
        
        return {
            "items": items,
            "total_items": total_items,
            "total_price": total_price
        }

    @staticmethod
    def add_to_cart(db: Session, user_id: int, cart_data: CartItemCreate):
        # 1. Check karein product exist karta hai ya nahi
        product = db.query(Product).filter(Product.id == cart_data.product_id, Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product nahi mila ya inactive hai")

        # 2. Stock check karein
        if product.stock < cart_data.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Itna stock nahi hai. Available stock: {product.stock}"
            )

        # 3. Check karein agar product pehle se cart mein hai toh quantity barha dein
        existing_item = db.query(CartItem).filter(
            CartItem.user_id == user_id, 
            CartItem.product_id == cart_data.product_id
        ).first()

        if existing_item:
            new_quantity = existing_item.quantity + cart_data.quantity
            if product.stock < new_quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart ki total quantity stock se barh rahi hai")
            existing_item.quantity = new_quantity
            db.commit()
            db.refresh(existing_item)
            return existing_item

        # 4. Agar naya item hai toh add karein
        new_item = CartItem(user_id=user_id, product_id=cart_data.product_id, quantity=cart_data.quantity)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        return new_item

    @staticmethod
    def update_cart_item(db: Session, user_id: int, item_id: int, update_data: CartItemUpdate):
        item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item nahi mila")

        # Stock validation fir se check hogi update par
        if item.product.stock < update_data.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Itna stock nahi hai. Available: {item.product.stock}")

        item.quantity = update_data.quantity
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def remove_from_cart(db: Session, user_id: int, item_id: int):
        item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item nahi mila")
        
        db.delete(item)
        db.commit()
        return {"detail": "Item cart se hata diya gaya hai"}

    @staticmethod
    def clear_cart(db: Session, user_id: int):
        db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        db.commit()
        return {"detail": "Cart poori tarah khali kar di gayi hai"}