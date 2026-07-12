import time
import pytest
from jose import jwt
from starlette.websockets import WebSocketDisconnect
from app.core.config import settings
from app.api.v1.endpoints.websocket_router import get_ws_user


def make_token(sub, exp_delta_seconds=3600, secret=None, alg=None):
    secret = secret or settings.SECRET_KEY
    alg = alg or settings.ALGORITHM
    payload = {"sub": sub, "exp": int(time.time()) + exp_delta_seconds}
    return jwt.encode(payload, secret, algorithm=alg)


class TestGetWsUser:

    def test_valid_token_with_numeric_sub_returns_int(self):
        token = make_token("42")
        assert get_ws_user(token) == 42

    def test_valid_token_with_string_sub_returns_string(self):
        token = make_token("user@example.com")
        assert get_ws_user(token) == "user@example.com"

    def test_expired_token_falls_back_and_still_returns_user(self):
        # exp pehle hi guzar chuka hai, code ka fallback (verify_exp=False) chalna chahiye
        token = make_token("7", exp_delta_seconds=-3600)
        assert get_ws_user(token) == 7

    def test_completely_malformed_token_returns_none(self):
        result = get_ws_user("this.is.not.a.valid.jwt")
        assert result is None

    def test_token_with_wrong_secret_returns_none(self):
        token = make_token("5", secret="totally-wrong-secret-key")
        assert get_ws_user(token) is None


class TestWebsocketConnectionAuth:

    def test_websocket_invalid_token_closes_with_4003(self, client):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/api/v1/ws?token=invalid.token.value") as websocket:
                websocket.receive_text()
        assert exc_info.value.code == 4003