# Крестики-нолики в Telegram Mini App

Мини-приложение Telegram, в котором пользователь играет в крестики-нолики против компьютера, получает промокод при победе, а бот отправляет результаты в личные сообщения.

## Ссылки
- Мини-апп: https://ttt.46.101.108.62.nip.io
- Бот: @wfu7t7rqo2h1_bot

## Возможности
- Поддержка Telegram Web Apps: корректная работа внутри клиента, валидация `initData` с HMAC и проверкой срока действия.
- Два уровня сложности ИИ (случайные ходы/улучшенный minimax с небольшим рандомом, чтобы победа была достижима).
- Промокод из пяти цифр при победе, уведомления о победе/поражении в бот.
- Обработка игры вне Telegram: показывается предупреждение.
- Логирование, health-check `/health`, отдельный endpoint `/api/result` для фиксирования исхода.

## Стек
- Backend: FastAPI, uvicorn, httpx, pydantic.
- Frontend: чистый HTML/CSS/JS + telegram-web-app.js.
- Инфраструктура: Dockerfile, Docker Compose, Traefik (через существующий `safeworkhub-network`), GitHub Actions.

## Быстрый старт локально
1. Скопируйте переменные: `cp .env.example .env` и заполните нужные поля. Для локали можно выставить `WEB_APP_URL=http://localhost:8000`, `APP_DOMAIN=localhost`, `TRAEFIK_NETWORK=bridge`.
2. Установите зависимости и запустите dev-сервер:
   ```bash
   make install-dev
   source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
3. Откройте `http://localhost:8000` или используйте Telegram Web App с тестовым `initData`.

## Запуск в Docker
- Локально: `docker compose up app` (при необходимости установите `TRAEFIK_NETWORK=bridge` в `.env`).
- Продакшн на сервере с traefik (уже настроен): заполните `.env` боевыми данными и выполните `docker compose up -d --build`. Сервис работает в `safeworkhub-network`, роутер и сервис прописаны в `/root/safeworkhub/infra/traefik/dynamic.yml`.

## Тесты и качество
- Линтинг: `make lint` (ruff).
- Формат: `ruff format .`
- Тесты: `make test` (pytest + проверка валидации initData и API).

## CI/CD
- `.github/workflows/ci.yml` — линтеры, тесты, сборка docker-образа на push/PR.
- `.github/workflows/deploy.yml` — деплой в `/opt/ttt-miniapp` по SSH и обновление webhook. Требуемые secrets: `SSH_HOST`, `SSH_USER`, `SSH_PASSWORD`, `SSH_PORT` (опционально), `APP_DOMAIN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TRAEFIK_NETWORK` (по умолчанию `safeworkhub-network`).

## Переменные окружения
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME` — данные бота.
- `WEB_APP_URL` — публичный URL мини-аппа (используется в кнопке).
- `APP_DOMAIN` — домен для Traefik/сертификатов.
- `APP_PORT` — порт uvicorn.
- `INIT_DATA_TTL_SECONDS` — допустимый возраст initData.
- `TRAEFIK_NETWORK` — имя внешней сети (для сервера: `safeworkhub-network`).
- `COMPOSE_PROJECT_NAME` — уникальное имя проекта docker compose.

Подробности по развёртыванию — в `docs/DEPLOYMENT.md`.

## Автор
Yan Bubenok — yan@bubenok.com
