# Архитектура

## Общая схема
- Телеграм-клиент открывает WebApp по кнопке из бота.
- Frontend (статическая сборка в `web/`) грузится из FastAPI и общается с backend по `/api/result`.
- Backend:
  - отдаёт статические файлы и health-check `/health`;
  - принимает Telegram webhook `/telegram/webhook` (команда `/start` шлёт кнопку с WebApp и выставляет menu button);
  - принимает результат игры `/api/result`, валидирует `initData`, генерирует промокод и отправляет сообщение пользователю через Bot API.
- Деплой: контейнер `app` в Docker, доступ наружу через Traefik (файл `/root/safeworkhub/infra/traefik/dynamic.yml`).

## Backend
- `app/main.py` — сборка FastAPI-приложения, StaticFiles-монтаж, DI для настроек и Telegram-клиента, ручки `/health`, `/telegram/webhook`, `/api/result`.
- `app/security.py` — валидация `initData` по документации Telegram:
  - парсинг query string, исключение `hash`;
  - `data-check-string` = пары key=value, отсортированные по ключу и соединённые `\n`;
  - `secret_key = HMAC_SHA256(bot_token, "WebAppData")`;
  - `expected_hash = HMAC_SHA256(data-check-string, secret_key)`, сравнение через `hmac.compare_digest`;
  - проверка `auth_date` на TTL (по умолчанию 24 часа);
  - извлечение `user.id` из `user` JSON.
- `app/telegram_client.py` — отправка сообщений/вебхуков в Bot API (httpx).
- `app/promo.py` — генерация криптографического 5-значного кода (secrets).
- `app/schemas.py` — Pydantic модели запросов/ответов, поддержка camelCase `initData` через валидатор.
- Логи — стандартный logging, единый формат. Health-check используется также в docker healthcheck.

## Frontend
- Файлы в `web/` (без сборщика): `index.html`, `styles.css`, `app.js`.
- Дизайн: мобильный-first, мягкие цвета, шрифт Manrope, плавные состояния, карточка промокода и кнопка копирования.
- Telegram WebApp API: `WebApp.ready()`, работа с `themeParams`, проверка наличия `window.Telegram`.
- Логика игры:
  - поле 3x3, хранится массивом;
  - два режима: `easy` (случайные/приоритетные клетки) и `smart` (minimax с небольшим рандомом для возможности победить);
  - обработка победы/поражения/ничьей, вызов backend с `result` и `init_data`;
  - при победе отображается промокод и кнопка копирования, при проигрыше — предложение сыграть ещё раз.
- Если WebApp открыт вне Telegram — показывается предупреждение и блокируется игра.

## Инфраструктура
- Dockerfile: python:3.13-slim, установка зависимостей, curl для healthcheck, запуск uvicorn от пользователя `app`.
- docker-compose.yml:
  - сервис `app` с healthcheck, лейблами Traefik, внешней сетью `${TRAEFIK_NETWORK}` (на сервере `safeworkhub-network`);
  - без собственного reverse-proxy: трафик идёт через Traefik (динамический конфиг по пути `/root/safeworkhub/infra/traefik/dynamic.yml` — добавлены router/service `ttt-miniapp`).
- GitHub Actions:
  - CI: линтинг, тесты, сборка docker-образа.
  - CD: упаковка артефакта, копирование на сервер `/opt/ttt-miniapp`, сборка/запуск `docker compose`, установка webhook.
- Скрипт `scripts/set_webhook.sh` для ручного обновления webhook (использует `TELEGRAM_BOT_TOKEN`, `WEBHOOK_URL`).

## Безопасность и конфигурация
- Все секреты только в `.env`/GitHub Secrets, в репозитории — только `.env.example`.
- Валидируются подпись и свежесть `initData`, используется `hmac.compare_digest`.
- Бот-API вызывается через httpx с таймаутом; ошибки оборачиваются в 502.
- Health-check `/health` (GET/HEAD) используется для docker и внешних проверок.

## Тесты
- `tests/test_security.py` — валидация initData (валидный кейс, неверная подпись, устаревшая подпись).
- `tests/test_promo.py` — формат и длина промокода.
- `tests/test_api.py` — API `/api/result` (happy-path, невалидная подпись), подмена Telegram-клиента.
