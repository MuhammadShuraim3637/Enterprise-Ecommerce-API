import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.category import Category
from app.models.product import Product
from app.core.security import get_password_hash

def test_review_submission_and_fetching(client: TestClient, db_session: Session):
    # 1. Base Setup (Category + Product + Regular User)
    category = Category(name="Apparel", slug="apparel")
    db_session.add(category)
    db_session.commit()

    product = Product(
        name="Winter Hoodie", slug="winter-hoodie", price=45.00,
        stock=10, category_id=category.id
    )
    db_session.add(product)

    user_email = "buyer@example.com"
    buyer = User(
        email=user_email, hashed_password=get_password_hash("buyerpass123"),
        full_name="Muhammad Ali", is_active=True, is_verified=True
    )
    db_session.add(buyer)
    db_session.commit()

    # 2. Login to act as verified buyer
    login_response = client.post("/api/v1/auth/login", json={"email": user_email, "password": "buyerpass123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Review
    review_payload = {
        "product_id": product.id,
        "rating": 5,
        "comment": "Outstanding fabric quality, highly recommended!"
    }
    post_res = client.post("/api/v1/reviews/", json=review_payload, headers=headers)
    assert post_res.status_code == 201
    assert post_res.json()["rating"] == 5
    assert post_res.json()["user"]["full_name"] == "Muhammad Ali"

    # 4. Fetch Reviews for this specific product
    get_res = client.get(f"/api/v1/reviews/product/{product.id}")
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1
    assert get_res.json()[0]["comment"] == "Outstanding fabric quality, highly recommended!"