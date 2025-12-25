import hashlib
import hmac
import time
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import get_app
from app.security import build_data_check_string


def build_init_data(bot_token: str, user_id: int) -> str:
    now = int(time.time())
    data = {
        "auth_date": str(now),
        "user": f'{{"id":{user_id},"first_name":"User"}}',
    }
    data_check_string = build_data_check_string(data)
    secret_key = hmac.new(
        bot_token.encode("utf-8"),
        msg=b"WebAppData",
        digestmod=hashlib.sha256,
    ).digest()
    signature = hmac.new(
        secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return urlencode({**data, "hash": signature})


class DummyTelegramClient:
    def __init__(self):
        self.sent = []

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        self.sent.append({"chat_id": chat_id, "text": text, "reply_markup": reply_markup})


def create_test_app():
    settings = Settings(
        telegram_bot_token="123:ABC",
        telegram_bot_username="bot",
        web_app_url="https://example.com",
        app_domain="example.com",
        app_port=8000,
        init_data_ttl_seconds=600,
        request_timeout=5.0,
    )
    app = get_app(settings)
    return app


def test_submit_result_success():
    app = create_test_app()
    dummy = DummyTelegramClient()
    with TestClient(app) as client:
        app.state.tg_client = dummy
        init_data = build_init_data(bot_token=app.state.settings.telegram_bot_token, user_id=77)
        response = client.post("/api/result", json={"result": "win", "init_data": init_data})
        assert response.status_code == 200
        payload = response.json()
        assert "promo_code" in payload and payload["promo_code"]
        assert len(payload["promo_code"]) == 5
        assert dummy.sent
        assert dummy.sent[0]["chat_id"] == 77
        assert dummy.sent[0]["text"].startswith("Победа!")


def test_submit_result_invalid_signature():
    app = create_test_app()
    dummy = DummyTelegramClient()
    with TestClient(app) as client:
        app.state.tg_client = dummy
        response = client.post("/api/result", json={"result": "win", "init_data": "hash=bad"})
        assert response.status_code == 401
        assert not dummy.sent
