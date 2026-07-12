def test_register_and_login_flow(client, db_session):
    # 1. Test user creation
    reg_response = client.post("/api/v1/auth/register", json={
        "email": "shuraim@example.com",
        "password": "supersecurepassword123",
        "full_name": "Muhammad Shuraim"
    })
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == "shuraim@example.com"

    # 1.5. Manually bypass email verification in Test DB (taake user active/verified ho jaye)
    from app.models.user import User
    user = db_session.query(User).filter(User.email == "shuraim@example.com").first()
    if user:
        user.is_verified = True
        user.is_active = True
        db_session.commit()

    # 2. Test login flow
    login_response = client.post("/api/v1/auth/login", json={
        "email": "shuraim@example.com",
        "password": "supersecurepassword123"
    })
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data

    access_token = login_data["access_token"]
    refresh_token = login_data["refresh_token"]

    # 3. Test /me Endpoint (Profile Check)
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)

    assert me_response.status_code == 200
    assert me_response.json()["email"] == "shuraim@example.com"

    # 4. Test /refresh Endpoint (Naya token lena)
    refresh_response = client.post(f"/api/v1/auth/refresh?refresh_token={refresh_token}")

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

    # 5. Test /logout Endpoint
    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_response.status_code in [200, 204]  # Kuch log 200 dete hain kuch 204 No Content


def test_register_duplicate_email(client, db_session):
    client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password12345",
        "full_name": "First User"
    })
    response = client.post("/api/v1/auth/register", json={
        "email": "duplicate@example.com",
        "password": "anotherpassword",
        "full_name": "Second User"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_wrong_password(client, db_session):
    client.post("/api/v1/auth/register", json={
        "email": "wrongpass@example.com",
        "password": "correctpassword123",
        "full_name": "Test User"
    })
    response = client.post("/api/v1/auth/login", json={
        "email": "wrongpass@example.com",
        "password": "incorrectpassword"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_nonexistent_user(client, db_session):
    response = client.post("/api/v1/auth/login", json={
        "email": "doesnotexist@example.com",
        "password": "somepassword123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_inactive_account(client, db_session):
    from app.models.user import User
    client.post("/api/v1/auth/register", json={
        "email": "inactive@example.com",
        "password": "password12345",
        "full_name": "Inactive User"
    })
    user = db_session.query(User).filter(User.email == "inactive@example.com").first()
    user.is_active = False
    db_session.commit()

    response = client.post("/api/v1/auth/login", json={
        "email": "inactive@example.com",
        "password": "password12345"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Account is disabled"


def test_me_endpoint_unverified_user_forbidden(client, db_session):
    client.post("/api/v1/auth/register", json={
        "email": "unverified@example.com",
        "password": "password12345",
        "full_name": "Unverified User"
    })
    login_response = client.post("/api/v1/auth/login", json={
        "email": "unverified@example.com",
        "password": "password12345"
    })
    access_token = login_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Please verify your email first"


def test_me_endpoint_invalid_token(client, db_session):
    headers = {"Authorization": "Bearer this.is.not.a.valid.token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_verify_email_invalid_token(client, db_session):
    response = client.get("/api/v1/auth/verify-email?token=invalid-token-xyz")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired verification token"


def test_forgot_password_nonexistent_email_still_200(client, db_session):
    # Security best practice: user existence leak nahi honi chahiye
    response = client.post("/api/v1/auth/forgot-password", json={
        "email": "ghostuser@example.com"
    })
    assert response.status_code == 200
    assert "message" in response.json()


def test_reset_password_invalid_token(client, db_session):
    response = client.post("/api/v1/auth/reset-password", json={
        "token": "invalid-reset-token",
        "new_password": "newpassword12345"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"


def test_refresh_token_invalid(client, db_session):
    response = client.post("/api/v1/auth/refresh?refresh_token=fake.invalid.token")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid refresh token"



def test_verify_email_success(client, db_session):
    from app.models.user import User
    client.post("/api/v1/auth/register", json={
        "email": "verifyme@example.com",
        "password": "password12345",
        "full_name": "Verify User"
    })
    user = db_session.query(User).filter(User.email == "verifyme@example.com").first()
    token = user.verification_token

    response = client.get(f"/api/v1/auth/verify-email?token={token}")
    assert response.status_code == 200

    db_session.refresh(user)
    assert user.is_verified is True


def test_forgot_password_existing_email_sets_token(client, db_session):
    from app.models.user import User
    client.post("/api/v1/auth/register", json={
        "email": "forgotme@example.com",
        "password": "password12345",
        "full_name": "Forgot User"
    })
    response = client.post("/api/v1/auth/forgot-password", json={
        "email": "forgotme@example.com"
    })
    assert response.status_code == 200

    user = db_session.query(User).filter(User.email == "forgotme@example.com").first()
    assert user.password_reset_token is not None


def test_reset_password_success(client, db_session):
    from app.models.user import User
    client.post("/api/v1/auth/register", json={
        "email": "resetme@example.com",
        "password": "oldpassword123",
        "full_name": "Reset User"
    })
    client.post("/api/v1/auth/forgot-password", json={"email": "resetme@example.com"})

    user = db_session.query(User).filter(User.email == "resetme@example.com").first()
    reset_token = user.password_reset_token

    response = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "newpassword456"
    })
    assert response.status_code == 200

    # naye password se login hona chahiye
    login_response = client.post("/api/v1/auth/login", json={
        "email": "resetme@example.com",
        "password": "newpassword456"
    })
    assert login_response.status_code == 200


def test_get_admin_user_forbidden_for_regular_user(client, db_session):
    from app.models.user import User
    client.post("/api/v1/auth/register", json={
        "email": "notadmin@example.com",
        "password": "password12345",
        "full_name": "Not Admin"
    })
    user = db_session.query(User).filter(User.email == "notadmin@example.com").first()
    user.is_verified = True
    user.is_active = True
    db_session.commit()

    login_response = client.post("/api/v1/auth/login", json={
        "email": "notadmin@example.com",
        "password": "password12345"
    })
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # koi bhi endpoint jo get_admin_user use karta ho, jaise category create
    response = client.post("/api/v1/categories/", json={"name": "Test Category"}, headers=headers)
    assert response.status_code == 403    