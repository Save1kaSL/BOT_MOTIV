#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ]; then
  echo "❌ Нет TELEGRAM_BOT_TOKEN"
  echo ""
  echo "Локально: создай файл .env (см. .env.example)"
  echo "Bothost:  панель → Переменные окружения → TELEGRAM_BOT_TOKEN=..."
  exit 1
fi

export DATA_DIR="${DATA_DIR:-/app/data}"
export DATABASE_PATH="${DATABASE_PATH:-$DATA_DIR/users.db}"

VENV="$ROOT/python_bot/.venv"
PYTHON=""

if [ -x "$VENV/bin/python" ]; then
  PYTHON="$VENV/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  echo "❌ Python не найден"
  exit 1
fi

if [ ! -x "$VENV/bin/python" ] && [ ! -f "$VENV/.deps_ok" ]; then
  echo "📦 Установка зависимостей..."
  "$PYTHON" -m pip install -q -r python_bot/requirements.txt
  mkdir -p "$VENV"
  touch "$VENV/.deps_ok"
fi

echo "🤖 Python RKO bot (aiogram 3)..."
echo "   DATA_DIR=$DATA_DIR"
echo "   DATABASE_PATH=$DATABASE_PATH"
exec "$PYTHON" "$ROOT/python_bot/main.py"
