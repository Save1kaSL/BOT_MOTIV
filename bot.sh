#!/usr/bin/env bash
# Главный запуск — Python RKO бот (aiogram 3), команда /offers
ROOT="$(cd "$(dirname "$0")" && pwd)"
exec "$ROOT/bot_py.sh"
