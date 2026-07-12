import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.category import Category
from app.models.user import User

def test_order_creation_and_management_flow(client: TestClient, db_session: Session):
    db = db_session
    
    # 1. Setup - Create a mock category and product
    category = Category(name="Electronics", slug="electronics")
    db.add(category)
    db.commit()

    product = Product(
        name="Test Laptop",
        slug="test-laptop",
        description="Powerful laptop",
        price=1000.0,
        stock=5,
        category_id=category.id
    )
    db.add(product)
    db.commit()

    # 2. Register via Endpoint
    user_data = {"email": "buyer@example.com", "password": "securepassword123", "full_name": "Buyer"}
    reg_res = client.post("/api/v1/auth/register", json=user_data)
    assert reg_res.status_code == 201

    # 3. Bypass Email Verification directly in DB state
    user = db.query(User).filter(User.email == "buyer@example.com").first()
    assert user is not None
    user.is_verified = True  # Yahan 403 bypass fix ho jayega
    db.commit()

    # 4. Login using JSON payload now that the user is verified
    login_payload = {"email": "buyer@example.com", "password": "securepassword123"}
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 5. Create Valid Order
    order_payload = {
        "shipping_address": "123 Main St, Lahore",
        "items": [
            {"product_id": product.id, "quantity": 2}
        ]
    }
    order_res = client.post("/api/v1/orders/", json=order_payload, headers=headers)
    assert order_res.status_code == 201
    order_json = order_res.json()
    assert order_json["total_price"] == 2000.0
    assert order_json["status"] == "pending"
    
    # Verify stock deduction
    db.refresh(product)
    assert product.stock == 3

    # 6. Fail Case: Order Quantity exceeding current stock
    failing_payload = {
        "shipping_address": "123 Main St, Lahore",
        "items": [
            {"product_id": product.id, "quantity": 10}
        ]
    }
    fail_res = client.post("/api/v1/orders/", json=failing_payload, headers=headers)
    assert fail_res.status_code == 400
    assert "Insufficient stock" in fail_res.json()["detail"]

    # 7. Fetch User Profile Orders
    my_orders_res = client.get("/api/v1/orders/my-orders", headers=headers)
    assert my_orders_res.status_code == 200
    assert len(my_orders_res.json()) == 1