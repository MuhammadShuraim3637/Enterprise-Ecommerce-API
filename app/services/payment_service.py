from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.payment import Payment, PaymentStatus
from app.models.order import Order, OrderStatus
from app.schemas.payment_schema import PaymentCreate
from app.utils.payment_gateway import DummyPaymentGateway

class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def process_order_payment(self, obj_in: PaymentCreate, user_id: int) -> Payment:
        # 1. Verify Order existence and ownership
        order = self.db.query(Order).filter(Order.id == obj_in.order_id, Order.user_id == user_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found or access denied")

        # 2. Check if already paid or processing
        existing_payment = self.db.query(Payment).filter(Payment.order_id == order.id).first()
        if existing_payment and existing_payment.status == PaymentStatus.SUCCESSFUL.value:
            raise HTTPException(status_code=400, detail="Order has already been successfully paid")

        # 3. Create or pull existing pending record
        if not existing_payment:
            payment_record = Payment(
                order_id=order.id,
                amount=order.total_price,
                status=PaymentStatus.PENDING.value
            )
            self.db.add(payment_record)
            self.db.flush()
        else:
            payment_record = existing_payment

        # 4. Fire external/dummy payment gateway
        gateway_result = DummyPaymentGateway.process_transaction(
            amount=order.total_price,
            card_number=obj_in.card_number
        )

        if gateway_result["success"]:
            payment_record.status = PaymentStatus.SUCCESSFUL.value
            payment_record.transaction_id = gateway_result["transaction_id"]
            order.status = "processing" # Payment clear hone pe status transitions to next state
        else:
            payment_record.status = PaymentStatus.FAILED.value
            # Inventory reversal logic yahan aa sakti hai agar business specs kahein

        self.db.commit()
        self.db.refresh(payment_record)
        
        if not gateway_result["success"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Payment processing failed: {gateway_result['error']}"
            )
            
        return payment_record

    def get_payment_details(self, order_id: int, user_id: int, is_admin: bool = False) -> Payment:
        if is_admin:
            # Admin ko sab payments dekh sakte hain
            payment = self.db.query(Payment).filter(Payment.order_id == order_id).first()
        else:
            # Normal users apni payments hi dekh sakte hain
            payment = self.db.query(Payment).join(Order).filter(
                Payment.order_id == order_id, 
                Order.user_id == user_id
            ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment entry not found")
        return payment