#!/usr/bin/env bash
# Старый Node-бот (SQLite, CRM, админ) — если нужен именно он
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "❌ Нет .env"
  exit 1
fi

set -a && source .env && set +a
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN//\'/}"
export TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN//\"/}"
export TELEGRAM_BOT_USERNAME="${TELEGRAM_BOT_USERNAME//@/}"

if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == postgresql* ]]; then
  export DATABASE_URL="file:./packages/db/prisma/bot.db"
fi

[ -z "$TELEGRAM_BOT_TOKEN" ] && echo "❌ TELEGRAM_BOT_TOKEN" && exit 1
[ ! -d node_modules ] && npm install --silent

SCHEMA=packages/db/prisma/schema.prisma
npx prisma generate --schema="$SCHEMA" >/dev/null 2>&1
DB_FILE="packages/db/prisma/bot.db"
[ ! -f "$DB_FILE" ] && npx prisma db push --schema="$SCHEMA" --accept-data-loss && npm run seed -w @bot-motiv/db 2>/dev/null || true

echo "🤖 Node-бот..."
exec npx tsx apps/bot/src/index.ts
