import pytest
from datetime import timedelta
from fastapi import status
from app.models.product import Product
from app.models.cart import CartItem
from app.models.user import User
from app.utils.token import create_jwt_token
from app.core.security import get_password_hash  # Agar password hash karne ki zaroorat ho

@pytest.fixture
def test_user(db_session):
    """ Test ke liye database mein aik temporary user create karne ka fixture """
    user = User(
        email="cartuser@example.com",
        hashed_password="mockhashedpassword",  # Test ke liye mock string
        is_active=True,
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """ `create_jwt_token` ko sahi parameters de kar auth headers banane ka fixture """
    # Aapki token.py ke mutabiq 3 parameters dene hain: subject, expires_delta, token_type
    token = create_jwt_token(
        subject=test_user.email,  # Agar token mein id jati hai toh str(test_user.id) kar dena
        expires_delta=timedelta(minutes=30),
        token_type="access"
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def setup_cart_data(db_session):
    """ Test items aur products setup karne ka fixture """
    # 1. Normal active product jis ka stock 10 hai
    product_1 = Product(
        category_id=1,
        name="Test Wireless Mouse",
        slug="test-wireless-mouse",
        description="A great mouse",
        price=25.00,
        stock=10,
        is_active=True
    )
    # 2. Low stock product jis ka stock sirf 2 hai
    product_2 = Product(
        category_id=1,
        name="Test Keyboard",
        slug="test-keyboard",
        description="Limited keyboard",
        price=50.00,
        stock=2,
        is_active=True
    )
    db_session.add_all([product_1, product_2])
    db_session.commit()
    db_session.refresh(product_1)
    db_session.refresh(product_2)

    return {"product_1": product_1, "product_2": product_2}


def test_add_to_cart_success(client, auth_headers, setup_cart_data):
    """Naya item cart mein kamyabi se add hona chahiye"""
    product = setup_cart_data["product_1"]
    payload = {"product_id": product.id, "quantity": 2}

    response = client.post("/api/v1/cart/", json=payload, headers=auth_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["product_id"] == product.id
    assert data["quantity"] == 2


def test_add_to_cart_increase_quantity(client, auth_headers, setup_cart_data):
    """Agar item pehle se cart mein ho toh quantity barhni chahiye"""
    product = setup_cart_data["product_1"]
    payload = {"product_id": product.id, "quantity": 2}

    # Pehli dafa add kiya
    client.post("/api/v1/cart/", json=payload, headers=auth_headers)
    # Doosri dafa wahi item 3 quantity ke sath add kiya
    payload["quantity"] = 3
    response = client.post("/api/v1/cart/", json=payload, headers=auth_headers)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["quantity"] == 5  # 2 + 3 = 5


def test_add_to_cart_out_of_stock(client, auth_headers, setup_cart_data):
    """Stock se zyada quantity add karne par error aana chahiye"""
    product = setup_cart_data["product_2"]  # Iska stock sirf 2 hai
    payload = {"product_id": product.id, "quantity": 5}

    response = client.post("/api/v1/cart/", json=payload, headers=auth_headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_cart_summary(client, auth_headers, setup_cart_data):
    """Cart summary sahi details aur values return kare"""
    product = setup_cart_data["product_1"]
    
    # Pehle cart mein kuch add kar dete hain
    client.post("/api/v1/cart/", json={"product_id": product.id, "quantity": 2}, headers=auth_headers)

    response = client.get("/api/v1/cart/", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 2
    assert len(data["items"]) == 1


def test_update_cart_item_quantity(client, auth_headers, db_session, test_user, setup_cart_data):
    """Cart item ki quantity ko update kiya ja sake"""
    product = setup_cart_data["product_1"]
    
    # DB mein direct fake item daal rahe hain testing ke liye
    cart_item = CartItem(user_id=test_user.id, product_id=product.id, quantity=1)
    db_session.add(cart_item)
    db_session.commit()
    db_session.refresh(cart_item)

    payload = {"quantity": 4}
    response = client.put(f"/api/v1/cart/{cart_item.id}", json=payload, headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["quantity"] == 4


def test_remove_item_from_cart(client, auth_headers, db_session, test_user, setup_cart_data):
    """Cart se kisi item ko remove karna"""
    product = setup_cart_data["product_1"]
    cart_item = CartItem(user_id=test_user.id, product_id=product.id, quantity=1)
    db_session.add(cart_item)
    db_session.commit()

    response = client.delete(f"/api/v1/cart/{cart_item.id}", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK


def test_clear_entire_cart(client, auth_headers, db_session, test_user, setup_cart_data):
    """Poori cart ko khali karna"""
    p1 = setup_cart_data["product_1"]
    
    db_session.add(CartItem(user_id=test_user.id, product_id=p1.id, quantity=1))
    db_session.commit()

    response = client.delete("/api/v1/cart/clear/all", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK