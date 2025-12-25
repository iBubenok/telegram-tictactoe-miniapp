from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataValidationError(Exception):
    def __init__(self, message: str, *, context: dict | None = None):
        super().__init__(message)
        self.context = context or {}


logger = logging.getLogger(__name__)


@dataclass
class ValidatedUser:
    user_id: int
    first_name: str | None
    username: str | None
    raw: dict[str, str]


def parse_init_data(init_data: str) -> tuple[dict[str, str], str]:
    if not init_data:
        raise InitDataValidationError("initData отсутствует")

    parsed: dict[str, str] = dict(
        parse_qsl(init_data, keep_blank_values=True, strict_parsing=False)
    )
    incoming_hash = parsed.pop("hash", None)
    if incoming_hash is None:
        raise InitDataValidationError("hash не найден")

    return parsed, incoming_hash


def build_data_check_string(data: dict[str, str]) -> str:
    return "\n".join(f"{k}={v}" for k, v in sorted(data.items()))


def validate_init_data(init_data: str, bot_token: str, max_age_seconds: int) -> ValidatedUser:
    data, incoming_hash = parse_init_data(init_data)

    try:
        auth_date = int(data.get("auth_date", "0"))
    except ValueError as exc:
        raise InitDataValidationError("auth_date некорректен") from exc

    if auth_date <= 0:
        raise InitDataValidationError("auth_date отсутствует")

    now = int(time.time())
    if now - auth_date > max_age_seconds:
        raise InitDataValidationError("initData устарел")

    data_check_string = build_data_check_string(data)
    logger.info(
        "initData received: keys=%s, auth_date=%s, len=%s, hash_prefix=%s",
        sorted(data.keys()),
        auth_date,
        len(init_data),
        incoming_hash[:8],
    )
    candidates: list[str] = []

    def add_candidate(secret: bytes, message: str) -> None:
        candidates.append(
            hmac.new(secret, msg=message.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
        )

    # Базовый способ (WebApp): HMAC(token, "WebAppData") как ключ.
    secret_key_webapp = hmac.new(
        bot_token.encode("utf-8"),
        msg=b"WebAppData",
        digestmod=hashlib.sha256,
    ).digest()
    add_candidate(secret_key_webapp, data_check_string)

    # Альтернативный способ (Login Widget) — для совместимости с клиентами:
    # ключ = SHA256(bot_token).
    hashed_token = hashlib.sha256(bot_token.encode("utf-8")).digest()
    add_candidate(hashed_token, data_check_string)

    # Переставленные аргументы HMAC (на случай ошибочной реализации клиента).
    add_candidate(
        hmac.new(b"WebAppData", msg=bot_token.encode("utf-8"), digestmod=hashlib.sha256).digest(),
        data_check_string,
    )

    # В некоторых клиентах подпись строится по «сырой» строке без URL-декодинга.
    raw_pairs: list[str] = []
    for segment in init_data.split("&"):
        if not segment:
            continue
        key, _, value = segment.partition("=")
        if key == "hash":
            continue
        raw_pairs.append(segment)
    if raw_pairs:
        raw_data_check = "\n".join(
            sorted(raw_pairs, key=lambda s: s.split("=", 1)[0])
        )
        add_candidate(secret_key_webapp, raw_data_check)
        add_candidate(hashed_token, raw_data_check)

    if not any(hmac.compare_digest(candidate, incoming_hash) for candidate in candidates):
        ctx = {
            "hash": incoming_hash,
            "auth_date": auth_date,
            "keys": sorted(data.keys()),
            "raw_len": len(init_data),
        }
        logger.warning("initData hash mismatch | %s", ctx)
        try:
            with open("/tmp/initdata-debug.log", "a", encoding="utf-8") as f:
                f.write(
                    f"{int(time.time())};auth_date={auth_date};keys={ctx['keys']};"
                    f"len={ctx['raw_len']};hash={incoming_hash[:16]};raw={init_data[:400]}\n"
                )
        except OSError:
            logger.debug("cannot write debug initdata file")

        raise InitDataValidationError(
            "подпись initData невалидна",
            context={"keys": sorted(data.keys()), "auth_date": auth_date},
        )

    user_json = data.get("user")
    if not user_json:
        raise InitDataValidationError("user отсутствует")

    try:
        user_data = json.loads(user_json)
    except json.JSONDecodeError as exc:
        raise InitDataValidationError("user некорректен") from exc

    user_id = user_data.get("id")
    if not isinstance(user_id, int):
        raise InitDataValidationError("user.id отсутствует")

    return ValidatedUser(
        user_id=user_id,
        first_name=user_data.get("first_name"),
        username=user_data.get("username"),
        raw=data,
    )
