import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.category import Category
from app.models.product import Product
from app.models.user import User

def test_payment_processing_flow(client: TestClient, db_session: Session):
    db = db_session

    # 1. Mock Category & Product Setup
    category = Category(name="Apparel", slug="apparel")
    db.add(category)
    db.commit()

    product = Product(
        name="Premium Jacket",
        slug="premium-jacket",
        description="Stylish winter jacket",
        price=150.00,
        stock=10,
        category_id=category.id
    )
    db.add(product)
    db.commit()

    # 2. Register and Force Verify User
    user_data = {"email": "payer@example.com", "password": "securepassword123", "full_name": "Payer"}
    client.post("/api/v1/auth/register", json=user_data)
    user = db.query(User).filter(User.email == "payer@example.com").first()
    user.is_verified = True
    db.commit()

    # 3. Login
    login_res = client.post("/api/v1/auth/login", json={"email": "payer@example.com", "password": "securepassword123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 4. Create Order
    order_payload = {
        "shipping_address": "456 Luxury Ave, Lahore",
        "items": [{"product_id": product.id, "quantity": 1}]
    }
    order_res = client.post("/api/v1/orders/", json=order_payload, headers=headers)
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # 5. Execute Successful Payment Simulation
    success_payment_payload = {
        "order_id": order_id,
        "card_number": "4242 4242 4242 4242",
        "cvv": "123",
        "expiry_date": "12/29"
    }
    pay_res = client.post("/api/v1/payments/", json=success_payment_payload, headers=headers)
    assert pay_res.status_code == 201
    pay_json = pay_res.json()
    assert pay_json["status"] == "successful"
    assert pay_json["transaction_id"].startswith("txn_")

    # 6. Execute Failure Case Simulation (Using blocked 5555 card)
    # Create another order first
    order_res2 = client.post("/api/v1/orders/", json=order_payload, headers=headers)
    order_id2 = order_res2.json()["id"]

    failing_payment_payload = {
        "order_id": order_id2,
        "card_number": "5555 0000 1111 2222",
        "cvv": "999",
        "expiry_date": "01/30"
    }
    fail_res = client.post("/api/v1/payments/", json=failing_payment_payload, headers=headers)
    assert fail_res.status_code == 400
    assert "Card declined" in fail_res.json()["detail"]