import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash

def test_users_endpoints_flow(client: TestClient, db_session: Session):
    # 1. Pehle normal user create karo aur active/verify karo
    reg_response = client.post("/api/v1/auth/register", json={
        "email": "shuraim_user@example.com",
        "password": "userpassword123",
        "full_name": "Shuraim User"
    })
    assert reg_response.status_code == 201
    
    user = db_session.query(User).filter(User.email == "shuraim_user@example.com").first()
    if user:
        user.is_verified = True
        user.is_active = True
        db_session.commit()

    # 2. Login karke access token uthao
    login_response = client.post("/api/v1/auth/login", json={
        "email": "shuraim_user@example.com",
        "password": "userpassword123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test GET /users/me
    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["full_name"] == "Shuraim User"

    # 4. Test PUT /users/me/update
    update_response = client.put("/api/v1/users/me/update", json={
        "full_name": "Muhammad Shuraim Updated"
    }, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Muhammad Shuraim Updated"

    # 5. Test Admin Check (Kyunki yeh normal user hai, isey all users par 403 Forbidden milna chahiye)
    admin_response = client.get("/api/v1/users/", headers=headers)
    assert admin_response.status_code == 403  # Not enough privileges


def test_admin_get_all_users(client: TestClient, db_session: Session):
    # 1. Ek test admin user create aur active/verify karo direct DB se
    admin_email = "admin_shuraim@example.com"
    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin Shuraim",
        is_active=True,
        is_verified=True,
        is_superuser=True  # Yeh check zaroori hai
    )
    db_session.add(admin_user)
    db_session.commit()

    # 2. Admin account se login karke token uthao
    login_response = client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "adminpassword123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test GET /users/ as Admin (Ab missing lines execute hongi)
    response = client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1