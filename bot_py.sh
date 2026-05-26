#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "❌ Нет .env"
  exit 1
fi

VENV="$ROOT/python_bot/.venv"

if [ ! -d "$VENV" ]; then
  echo "📦 venv..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q -r python_bot/requirements.txt
fi

echo "🤖 Python RKO bot (aiogram 3)..."
exec "$VENV/bin/python" "$ROOT/python_bot/main.py"
