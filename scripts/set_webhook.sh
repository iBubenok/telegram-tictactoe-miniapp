#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN не задан" >&2
  exit 1
fi

if [[ -z "${WEBHOOK_URL:-}" ]]; then
  echo "WEBHOOK_URL не задан" >&2
  exit 1
fi

ALLOWED_UPDATES='["message","callback_query","my_chat_member"]'

curl -sSf -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=${WEBHOOK_URL}" \
  -d "allowed_updates=${ALLOWED_UPDATES}"

echo
echo "Webhook обновлён на ${WEBHOOK_URL}"
