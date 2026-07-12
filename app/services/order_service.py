import asyncio
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order_schema import OrderCreate, OrderStatusUpdate
from app.services.websocket_manager import ws_manager

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_order(self, obj_in: OrderCreate, user_id: int) -> Order:
        if not obj_in.items:
            raise HTTPException(status_code=400, detail="Order must contain at least one item")

        validated_items = []
        calculated_total = Decimal("0.0")

        # Step 1: Query products with row locking to prevent race conditions
        for item in obj_in.items:
            # .with_for_update() row ko lock kar deta hai jab tak transaction commit/rollback na ho
            product = self.db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {item.product_id} not found")

            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for '{product.name}'. Available: {product.stock}"
                )

            validated_items.append((product, item.quantity))
            calculated_total += Decimal(str(product.price)) * item.quantity

        # Step 2: Create Order
        db_order = Order(
            user_id=user_id,
            shipping_address=obj_in.shipping_address,
            total_price=calculated_total,
            status=OrderStatus.PENDING.value
        )
        self.db.add(db_order)
        self.db.flush()  # Order ID generate karne ke liye

        # Step 3: Order Items add karein aur inventory update karein
        for product, quantity in validated_items:
            # Deduct Inventory Stock (Safely locked)
            product.stock -= quantity
            
            db_item = OrderItem(
                order_id=db_order.id,
                product_id=product.id,
                quantity=quantity,
                price=product.price
            )
            self.db.add(db_item)

        self.db.commit()
        self.db.refresh(db_order)
        return db_order

    def get_order_by_id(self, order_id: int) -> Order:
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    def get_user_orders(self, user_id: int) -> list[Order]:
        return self.db.query(Order).filter(Order.user_id == user_id).all()

    def get_all_orders(self) -> list[Order]:
        return self.db.query(Order).all()

    def update_order_status(self, order_id: int, obj_in: OrderStatusUpdate) -> Order:
        db_order = self.get_order_by_id(order_id)
        
        old_status = db_order.status
        new_status = obj_in.status.value

        # Rollback Stock Logic: Agar order pehle cancel nahi tha aur ab cancel ho raha hai
        if old_status != OrderStatus.CANCELLED.value and new_status == OrderStatus.CANCELLED.value:
            for item in db_order.items:
                # Product ko fetch karke wapis stock plus (rollback) karenge
                product = self.db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
                if product:
                    product.stock += item.quantity

        db_order.status = new_status
        self.db.commit()
        self.db.refresh(db_order)

        # Real-time WebSocket live update broadcast logic
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        payload = {
            "type": "order_update",
            "order_id": db_order.id,
            "status": db_order.status
        }

        if loop.is_running():
            asyncio.ensure_future(ws_manager.send_personal_message(payload, user_id=db_order.user_id))
        else:
            loop.run_until_complete(ws_manager.send_personal_message(payload, user_id=db_order.user_id))

        return db_order