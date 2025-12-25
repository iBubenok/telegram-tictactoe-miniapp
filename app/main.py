from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import Settings
from .promo import generate_promo_code
from .schemas import GameResult, ResultRequest, ResultResponse, WebhookUpdate
from .security import InitDataValidationError, validate_init_data
from .telegram_client import TelegramClient

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"


def configure_logging(level: str) -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    logging.getLogger().setLevel(numeric_level)


def get_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        http_client = httpx.AsyncClient(timeout=settings.request_timeout)
        app.state.settings = settings
        app.state.http_client = http_client
        app.state.tg_client = TelegramClient(settings, http_client)
        try:
            yield
        finally:
            await http_client.aclose()

    app = FastAPI(
        title="Tic Tac Toe Mini App",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )

    def get_telegram_client(request: Request) -> TelegramClient:
        return request.app.state.tg_client

    def get_settings(request: Request) -> Settings:
        return request.app.state.settings

    @app.api_route("/health", methods=["GET", "HEAD"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async def handle_start(tg: TelegramClient, chat_id: int, first_name: str | None = None) -> None:
        welcome = "Привет! Готовы сыграть в крестики-нолики? Я открою игру прямо внутри Telegram."
        if first_name:
            welcome = f"{first_name}, {welcome}"
        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "Играть",
                        "web_app": {"url": str(settings.web_app_url)},
                    }
                ]
            ]
        }
        await tg.send_message(chat_id=chat_id, text=welcome, reply_markup=keyboard)
        await tg.set_menu_button(chat_id)

    @app.post("/telegram/webhook")
    async def telegram_webhook(
        update: WebhookUpdate,
        tg: TelegramClient = Depends(get_telegram_client),
    ) -> JSONResponse:
        message = update.message
        if message is None and update.callback_query:
            message = update.callback_query.get("message")

        if not message:
            return JSONResponse({"ok": True})

        chat = message.get("chat") if isinstance(message, dict) else None
        chat_id = chat.get("id") if chat else None
        first_name = None
        if chat and isinstance(chat, dict):
            first_name = chat.get("first_name")

        text = ""
        if isinstance(message, dict):
            text = message.get("text") or ""
        if chat_id and text.startswith("/start"):
            await handle_start(tg, chat_id=chat_id, first_name=first_name)

        return JSONResponse({"ok": True})

    @app.post("/api/result", response_model=ResultResponse)
    async def submit_result(
        payload: ResultRequest,
        tg: TelegramClient = Depends(get_telegram_client),
        settings: Settings = Depends(get_settings),
    ) -> ResultResponse:
        logging.getLogger("app.api").info(
            "submit_result received: result=%s, init_len=%s",
            payload.result,
            len(payload.init_data or ""),
        )
        try:
            validated = validate_init_data(
                payload.init_data,
                bot_token=settings.telegram_bot_token,
                max_age_seconds=settings.init_data_ttl_seconds,
            )
        except InitDataValidationError as exc:
            logging.getLogger("app.security").warning(
                "initData rejected: %s | ctx=%s", exc, getattr(exc, "context", None)
            )
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        promo_code = None
        message_text = "Ничья."
        if payload.result == GameResult.win:
            promo_code = generate_promo_code()
            message_text = f"Победа! Промокод выдан: {promo_code}"
        elif payload.result == GameResult.lose:
            message_text = "Проигрыш"

        try:
            await tg.send_message(chat_id=validated.user_id, text=message_text)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Ошибка отправки сообщения: {exc}",
            ) from exc

        return ResultResponse(promo_code=promo_code)

    if WEB_DIR.exists():
        app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="webapp")

    return app


app = get_app()
