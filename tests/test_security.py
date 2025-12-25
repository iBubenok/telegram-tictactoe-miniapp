import hashlib
import hmac
import time
from urllib.parse import urlencode

import pytest

from app.security import InitDataValidationError, build_data_check_string, validate_init_data


def build_init_data(bot_token: str, data: dict[str, str]) -> str:
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
    params = {**data, "hash": signature}
    return urlencode(params)


def test_validate_init_data_success():
    token = "123:ABC"
    now = int(time.time())
    data = {
        "auth_date": str(now),
        "query_id": "test_query",
        "user": '{"id":42,"first_name":"Test","username":"tester"}',
    }
    init_data = build_init_data(token, data)

    validated = validate_init_data(init_data, bot_token=token, max_age_seconds=60)
    assert validated.user_id == 42
    assert validated.first_name == "Test"
    assert validated.username == "tester"


def test_validate_init_data_invalid_hash():
    token = "123:ABC"
    now = int(time.time())
    wrong_init_data = f"auth_date={now}&user=%7B%22id%22%3A1%7D&hash=deadbeef"
    with pytest.raises(InitDataValidationError):
        validate_init_data(wrong_init_data, bot_token=token, max_age_seconds=120)


def test_validate_init_data_expired():
    token = "123:ABC"
    old = int(time.time()) - 10_000
    data = {
        "auth_date": str(old),
        "user": '{"id":1}',
    }
    init_data = build_init_data(token, data)
    with pytest.raises(InitDataValidationError):
        validate_init_data(init_data, bot_token=token, max_age_seconds=100)
