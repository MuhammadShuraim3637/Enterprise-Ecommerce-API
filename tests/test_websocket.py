import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.order import Order, OrderStatus


def test_websocket_order_status_broadcast(client: TestClient, db_session: Session):
    db = db_session

    user_data = {"email": "ws_user@example.com", "password": "securepassword123", "full_name": "WS Consumer"}
    client.post("/api/v1/auth/register", json=user_data)
    user = db.query(User).filter(User.email == "ws_user@example.com").first()
    user.is_verified = True
    db.commit()

    login_res = client.post(
        "/api/v1/auth/login", json={"email": "ws_user@example.com", "password": "securepassword123"}
    )
    token = login_res.json()["access_token"]

    with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        mock_order = Order(user_id=user.id, shipping_address="Test House 1", total_price=50.00, status="pending")
        db.add(mock_order)
        db.commit()

        from app.services.order_service import OrderService
        from app.schemas.order_schema import OrderStatusUpdate

        order_service = OrderService(db)
        order_service.update_order_status(mock_order.id, OrderStatusUpdate(status=OrderStatus.SHIPPED))

        ws_order_data = websocket.receive_json()
        assert ws_order_data["type"] == "order_update"
        assert ws_order_data["status"] == "shipped"


def test_websocket_customer_chat_forwarded_to_admin_and_reply(client: TestClient, db_session: Session):
    db = db_session

    # 1. Regular (non-admin) customer register aur verify karein
    client.post(
        "/api/v1/auth/register",
        json={"email": "cust_ws@example.com", "password": "securepassword123", "full_name": "Customer"},
    )
    customer = db.query(User).filter(User.email == "cust_ws@example.com").first()
    customer.is_verified = True
    db.commit()
    cust_login = client.post(
        "/api/v1/auth/login", json={"email": "cust_ws@example.com", "password": "securepassword123"}
    )
    cust_token = cust_login.json()["access_token"]

    # 2. Admin register aur verify karein
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin_ws@example.com", "password": "securepassword123", "full_name": "Admin"},
    )
    admin = db.query(User).filter(User.email == "admin_ws@example.com").first()
    admin.is_verified = True
    admin.is_superuser = True
    db.commit()
    admin_login = client.post(
        "/api/v1/auth/login", json={"email": "admin_ws@example.com", "password": "securepassword123"}
    )
    admin_token = admin_login.json()["access_token"]

    # 3. Connections testing
    with client.websocket_connect(f"/api/v1/ws?token={admin_token}") as admin_ws:
        with client.websocket_connect(f"/api/v1/ws?token={cust_token}") as cust_ws:
            # Customer sends a support message
            cust_ws.send_json({"type": "chat", "message": "Hello Agent"})

            # Admin receives it -> payload keys now match the new router structure
            admin_received = admin_ws.receive_json()
            assert admin_received["type"] == "chat_message"
            assert admin_received["from"] == customer.id  # Email ki jagah ab Integer ID check hogi 👈
            assert admin_received["email"] == "cust_ws@example.com"
            assert admin_received["message"] == "Hello Agent"

            # Admin replies directly to that customer using their customer.id
            admin_ws.send_json(
                {"type": "chat_reply", "to": customer.id, "message": "How can I help?"} # target custom.id 👈
            )

            # Customer receives the response
            cust_received = cust_ws.receive_json()
            assert cust_received["type"] == "chat_response"
            assert "How can I help?" in cust_received["message"]