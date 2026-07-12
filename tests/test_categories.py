import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash

def test_category_crud_flow(client: TestClient, db_session: Session):
    # 1. Admin setup direct in test DB
    admin_email = "admin_cat@example.com"
    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash("adminsecure123"),
        full_name="Admin Cat",
        is_active=True,
        is_verified=True,
        is_superuser=True
    )
    db_session.add(admin_user)
    db_session.commit()

    # Login karke admin token lo
    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "adminsecure123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test POST /categories/ (Admin Route)
    create_response = client.post("/api/v1/categories/", json={
        "name": "Smart Inverter Tech",
        "description": "High performance smart appliances"
    }, headers=headers)
    assert create_response.status_code == 201
    assert create_response.json()["slug"] == "smart-inverter-tech"
    category_id = create_response.json()["id"]

    # 3. Test GET /categories/ (Public Route - No headers needed)
    list_response = client.get("/api/v1/categories/")
    assert list_response.status_code == 200
    assert len(list_response.json()) >= 1

    # 4. Test PUT /categories/{id} (Admin Route)
    update_response = client.put(f"/api/v1/categories/{category_id}", json={
        "name": "Smart Inverter Appliances"
    }, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["slug"] == "smart-inverter-appliances"


def test_update_category_not_found(client: TestClient, db_session: Session):
    # Admin setup for authorization
    from app.models.user import User
    from app.core.security import get_password_hash
    
    admin_email = "admin_cat_edge@example.com"
    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash("adminsecure123"),
        full_name="Admin Edge",
        is_active=True,
        is_verified=True,
        is_superuser=True
    )
    db_session.add(admin_user)
    db_session.commit()

    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "adminsecure123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test PUT with non-existing ID (e.g., 9999) to hit line 39 & service line 36
    response = client.put("/api/v1/categories/9999", json={
        "name": "Non Existing Category"
    }, headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_regular_user_cannot_create_category(client: TestClient, db_session: Session):
    # 1. Regular user register aur active karo
    reg_response = client.post("/api/v1/auth/register", json={
        "email": "regular_cat_test@example.com",
        "password": "userpassword123",
        "full_name": "Regular Tester"
    })
    
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "regular_cat_test@example.com").first()
    if user:
        user.is_verified = True
        user.is_active = True
        db_session.commit()

    # 2. Regular user se login karke token uthao
    login_response = client.post("/api/v1/auth/login", json={
        "email": "regular_cat_test@example.com",
        "password": "userpassword123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Regular user category create karne ki koshish karega -> 403 Forbidden
    response = client.post("/api/v1/categories/", json={
        "name": "Hack Category",
        "description": "User trying to bypass admin roles"
    }, headers=headers)
    assert response.status_code == 403