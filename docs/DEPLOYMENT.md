# Деплой и эксплуатация

## Требования
- Docker + Docker Compose v2 на сервере.
- Внешняя сеть Traefik: `safeworkhub-network` (используется существующим traefik).
- Домен с HTTPS (используется `ttt.46.101.108.62.nip.io`, сертификат Let’s Encrypt выдаётся Traefik).

## Подготовка окружения
1. Заполните `.env` на сервере (`/opt/ttt-miniapp/.env`):
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_BOT_USERNAME=...
   WEB_APP_URL=https://<ваш_домен>
   APP_DOMAIN=<ваш_домен>
   APP_PORT=8000
   INIT_DATA_TTL_SECONDS=86400
   TRAEFIK_NETWORK=safeworkhub-network
   COMPOSE_PROJECT_NAME=tictactoe-miniapp
   ```
2. Убедитесь, что Traefik знает о новом сервисе: в `/root/safeworkhub/infra/traefik/dynamic.yml` добавлены блоки
   ```yaml
   http:
     routers:
       ttt-miniapp:
         rule: Host(`<ваш_домен>`)
         entryPoints: [websecure]
         service: ttt-miniapp
         middlewares: [global-ratelimit]
         tls:
           certResolver: letsencrypt
     services:
       ttt-miniapp:
         loadBalancer:
           servers:
             - url: http://tictactoe-miniapp-app-1:8000
   ```
   Файл уже обновлён для `ttt.46.101.108.62.nip.io`; при смене домена/названия контейнера обновите соответствующие строки. Traefik перезагружает конфиг автоматически (`providers.file.watch=true`).

## Деплой через Docker Compose
```bash
cd /opt/ttt-miniapp
docker compose pull || true   # для зависимости traefik сеть уже существует
docker compose up -d --build --remove-orphans
```
- Контейнер подключается к `safeworkhub-network`, порты 80/443 не занимались напрямую (Traefik проксирует).
- Проверка: `curl https://<домен>/health`.

## Обновление webhook
- Скрипт: `TELEGRAM_BOT_TOKEN=... WEBHOOK_URL=https://<домен>/telegram/webhook ./scripts/set_webhook.sh`
- Проверка: `curl -s https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo`

## CI/CD (GitHub Actions)
- `ci.yml` — линт/тест/сборка образа.
- `deploy.yml` — копирует tar на сервер и выполняет `docker compose up -d --build`, затем ставит webhook.
- Необходимые secrets: `SSH_HOST`, `SSH_USER`, `SSH_PASSWORD`, `SSH_PORT` (опционально), `APP_DOMAIN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TRAEFIK_NETWORK` (по умолчанию `safeworkhub-network`).
- Важно: файл `/root/safeworkhub/infra/traefik/dynamic.yml` должен содержать router/service `ttt-miniapp`; обновления Traefik извне не должны его затирать.

## Локальная разработка
- В `.env` выставьте `TRAEFIK_NETWORK=bridge`, `APP_DOMAIN=localhost`, `WEB_APP_URL=http://localhost:8000`.
- Запуск через uvicorn:
  ```bash
  make install-dev
  source .venv/bin/activate
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
- Или Docker: `docker compose up app` (используется встроенная сеть `bridge`).

## Проверки после развёртывания
- `https://<домен>/health` — 200.
- `getWebhookInfo` — без ошибок, `pending_update_count=0`.
- В Telegram: `/start` в боте -> кнопка «Играть» открывает мини-апп, игра работает, промокод появляется при победе, сообщения о победе/поражении приходят в чат.
