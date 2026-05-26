import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _clean(value: str | None) -> str:
    return (value or "").strip().strip("'\"")


BOT_TOKEN = _clean(os.getenv("TELEGRAM_BOT_TOKEN"))
TELEGRAM_PROXY = _clean(os.getenv("TELEGRAM_PROXY")) or None
ADMIN_IDS = {
    int(x.strip())
    for x in _clean(os.getenv("ADMIN_TELEGRAM_IDS", "")).split(",")
    if x.strip().isdigit()
}


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS
