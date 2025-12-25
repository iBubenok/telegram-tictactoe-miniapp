import logging
from typing import Any

import httpx

from .config import Settings

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient):
        self.settings = settings
        self.http = http_client
        self.base_url = settings.bot_api_base

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        response = await self.http.post(f"{self.base_url}/sendMessage", json=payload)
        if response.status_code != 200:
            logger.error("Не удалось отправить сообщение: %s", response.text)
            response.raise_for_status()

    async def answer_callback(self, callback_query_id: str, text: str | None = None) -> None:
        payload: dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        response = await self.http.post(f"{self.base_url}/answerCallbackQuery", json=payload)
        if response.status_code != 200:
            logger.error("Не удалось ответить на callback_query: %s", response.text)
            response.raise_for_status()

    async def set_webhook(self, url: str) -> None:
        payload = {"url": url, "allowed_updates": ["message", "callback_query", "my_chat_member"]}
        response = await self.http.post(f"{self.base_url}/setWebhook", json=payload)
        if response.status_code != 200:
            logger.error("setWebhook неуспешен: %s", response.text)
            response.raise_for_status()

    async def set_menu_button(self, chat_id: int) -> None:
        payload = {
            "chat_id": chat_id,
            "menu_button": {
                "type": "web_app",
                "text": "Играть",
                "web_app": {"url": str(self.settings.web_app_url)},
            },
        }
        response = await self.http.post(f"{self.base_url}/setChatMenuButton", json=payload)
        if response.status_code != 200:
            logger.warning("setChatMenuButton неуспешен: %s", response.text)
