import time
from datetime import timedelta
from jose import jwt
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)


class TestPasswordHashing:

    def test_hash_and_verify_correct_password(self):
        plain = "mysecurepassword123"
        hashed = get_password_hash(plain)

        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_verify_incorrect_password_returns_false(self):
        hashed = get_password_hash("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_with_corrupt_hash_returns_false(self):
        # Ye "except Exception: return False" branch ko cover karega
        result = verify_password("anypassword", "not-a-valid-bcrypt-hash")
        assert result is False

    def test_verify_password_with_empty_hash_returns_false(self):
        result = verify_password("anypassword", "")
        assert result is False

    def test_two_hashes_of_same_password_are_different(self):
        # bcrypt salt ki wajah se har hash unique hona chahiye
        hash1 = get_password_hash("samepassword")
        hash2 = get_password_hash("samepassword")
        assert hash1 != hash2
        # lekin dono verify hone chahiye
        assert verify_password("samepassword", hash1) is True
        assert verify_password("samepassword", hash2) is True


class TestAccessToken:

    def test_create_access_token_default_expiry(self):
        token = create_access_token(subject="testuser@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == "testuser@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        custom_delta = timedelta(minutes=5)
        token = create_access_token(subject="user123", expires_delta=custom_delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_create_access_token_subject_converted_to_string(self):
        # subject int ho to bhi string mein convert hona chahiye
        token = create_access_token(subject=12345)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "12345"


class TestRefreshToken:

    def test_create_refresh_token_default_expiry(self):
        token = create_refresh_token(subject="testuser@example.com")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == "testuser@example.com"
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_create_refresh_token_custom_expiry(self):
        custom_delta = timedelta(days=1)
        token = create_refresh_token(subject="user456", expires_delta=custom_delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert payload["sub"] == "user456"
        assert payload["type"] == "refresh"

    def test_access_and_refresh_tokens_have_different_types(self):
        access = create_access_token(subject="user789")
        refresh = create_refresh_token(subject="user789")

        access_payload = jwt.decode(access, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_payload = jwt.decode(refresh, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert access_payload["type"] == "access"
        assert refresh_payload["type"] == "refresh"
        assert access_payload["type"] != refresh_payload["type"]