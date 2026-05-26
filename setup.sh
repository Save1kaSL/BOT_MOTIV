#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

[ ! -f .env ] && cp .env.example .env && echo "✏️  Заполни .env (токен, ADMIN_TELEGRAM_IDS)" && exit 0

# SQLite в .env
if grep -q '^DATABASE_URL=postgresql' .env 2>/dev/null; then
  sed -i '' 's|^DATABASE_URL=.*|DATABASE_URL=file:./packages/db/prisma/bot.db|' .env 2>/dev/null \
    || sed -i 's|^DATABASE_URL=.*|DATABASE_URL=file:./packages/db/prisma/bot.db|' .env
  echo "ℹ️  .env → SQLite"
fi

npm install
export DATABASE_URL="${DATABASE_URL:-file:./packages/db/prisma/bot.db}"
npx prisma db push --schema=packages/db/prisma/schema.prisma --accept-data-loss
npm run seed -w @bot-motiv/db 2>/dev/null || npx tsx packages/db/prisma/seed.ts

chmod +x bot.sh
echo "✅ Готово → ./bot.sh"
