import pytest
from datetime import timedelta
from fastapi import status
from app.models.product import Product
from app.models.category import Category  
from app.models.user import User
from app.models.order import OrderStatus
from app.utils.token import create_jwt_token

@pytest.fixture
def user_headers(db_session):
    """Normal user generate karke auth headers dene ka fixture"""
    user = db_session.query(User).filter(User.email == "customer@example.com").first()
    if not user:
        user = User(
            email="customer@example.com", 
            hashed_password="hashed_password", 
            is_active=True, 
            is_verified=True,
            is_superuser=False,  # Normal Customer
            
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    
    token = create_jwt_token(subject=user.email, expires_delta=timedelta(minutes=30), token_type="access")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(db_session):
    """Admin user generate karke status updates ke liye headers dene ka fixture"""
    admin = db_session.query(User).filter(User.email == "admin@example.com").first()
    if not admin:
        admin = User(
            email="admin@example.com", 
            hashed_password="hashed_password", 
            is_active=True, 
            is_verified=True,
            is_superuser=True,       # <--- FIXED: Fixed the field and matching the endpoint logic
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    
    token = create_jwt_token(subject=admin.email, expires_delta=timedelta(minutes=30), token_type="access")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_product(db_session):
    """Testing ke liye dynamic product create karne ka fixture"""
    category = db_session.query(Category).filter(Category.slug == "test-stock-cat").first()
    if not category:
        category = Category(
            name="Test Stock Category",
            slug="test-stock-cat",
            description="Temporary category for testing stock management"
        )
        db_session.add(category)
        db_session.commit()
        db_session.refresh(category)

    product = Product(
        name="Test Stock Item",
        slug="test-stock-item",  
        category_id=category.id,  
        description="A product for testing inventory management",
        price=100.0,
        stock=10,  
        is_active=True
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


# ==========================================
#              TEST CASES
# ==========================================

def test_order_placement_deducts_stock(client, db_session, user_headers, test_product):
    """1. Order place karne par product stock deduct hona chahiye"""
    order_data = {
        "items": [{"product_id": test_product.id, "quantity": 3}],
        "shipping_address": "123 Test Street"
    }
    
    response = client.post("/api/v1/orders/", json=order_data, headers=user_headers)
    assert response.status_code == status.HTTP_201_CREATED
    
    db_session.refresh(test_product)
    assert test_product.stock == 7  # 10 - 3 = 7


def test_order_placement_insufficient_stock(client, db_session, user_headers, test_product):
    """2. Agar quantity stock se zyada ho, toh 400 Bad Request milna chahiye"""
    order_data = {
        "items": [{"product_id": test_product.id, "quantity": 15}],  
        "shipping_address": "123 Test Street"
    }
    
    response = client.post("/api/v1/orders/", json=order_data, headers=user_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    db_session.refresh(test_product)
    assert test_product.stock == 10


def test_order_cancellation_rolls_back_stock(client, db_session, user_headers, admin_headers, test_product):
    """3. Order cancel hone par items ka stock wapas restore (rollback) hona chahiye"""
    # Step A: Pehle order place karein
    order_data = {
        "items": [{"product_id": test_product.id, "quantity": 4}],
        "shipping_address": "123 Test Street"
    }
    response = client.post("/api/v1/orders/", json=order_data, headers=user_headers)
    assert response.status_code == status.HTTP_201_CREATED
    order_id = response.json()["id"]
    
    db_session.refresh(test_product)
    assert test_product.stock == 6  # 10 - 4 = 6
    
    # Step B: Admin headers aur PATCH method use karke order cancel karein
    status_update = {"status": OrderStatus.CANCELLED.value}
    cancel_response = client.patch(f"/api/v1/orders/{order_id}/status", json=status_update, headers=admin_headers)
    assert cancel_response.status_code == status.HTTP_200_OK
    
    # Final Verify: Stock wapas 10 ho jana chahiye
    db_session.refresh(test_product)
    assert test_product.stock == 10