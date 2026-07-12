import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.category import Category
from app.core.security import get_password_hash

def test_product_complete_flow(client: TestClient, db_session: Session):
    # 1. Admin setup & Category creation prerequisite
    admin_email = "admin_prod@example.com"
    admin_user = User(
        email=admin_email, hashed_password=get_password_hash("adminsecure123"),
        full_name="Admin Prod", is_active=True, is_verified=True, is_superuser=True
    )
    db_session.add(admin_user)
    
    category = Category(name="Electronics", slug="electronics")
    db_session.add(category)
    db_session.commit()

    # Login to get admin token
    login_response = client.post("/api/v1/auth/login", json={"email": admin_email, "password": "adminsecure123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test POST /products/ (Product Creation)
    prod_response = client.post("/api/v1/products/", json={
        "name": "Samsung S25 FE",
        "description": "Premium ecosystem smartphone",
        "price": "799.99",
        "stock": 50,
        "category_id": category.id
    }, headers=headers)
    assert prod_response.status_code == 201
    assert prod_response.json()["slug"] == "samsung-s25-fe"
    product_id = prod_response.json()["id"]

    # 3. Test POST /products/{id}/upload-image (Query Parameter fixed string parsing)
    file_data = {"file": ("test_phone.jpg", io.BytesIO(b"fakeimagebytes"), "image/jpeg")}
    img_response = client.post(
        f"/api/v1/products/{product_id}/upload-image?is_primary=true", 
        files=file_data, 
        headers=headers
    )
    assert img_response.status_code == 200
    assert img_response.json()["is_primary"] is True

    # 4. Test GET /products/ (List verification)
    list_response = client.get("/api/v1/products/")
    assert list_response.status_code == 200
    assert len(list_response.json()[0]["images"]) == 1