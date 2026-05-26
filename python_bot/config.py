import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _clean(value: str | None) -> str:
    return (value or "").strip().strip("'\"")


def _resolve_data_dir() -> Path:
    custom = _clean(os.getenv("DATA_DIR"))
    if custom:
        return Path(custom)
    return ROOT / "python_bot" / "data"


def _resolve_db_path() -> Path:
    for key in ("DATABASE_PATH", "DB_PATH"):
        custom = _clean(os.getenv(key))
        if custom:
            return Path(custom)
    return _resolve_data_dir() / "users.db"


DATA_DIR = _resolve_data_dir()
DB_PATH = _resolve_db_path()


BOT_TOKEN = _clean(os.getenv("TELEGRAM_BOT_TOKEN"))
TELEGRAM_PROXY = _clean(os.getenv("TELEGRAM_PROXY")) or None
ADMIN_IDS = {
    int(x.strip())
    for x in _clean(os.getenv("ADMIN_TELEGRAM_IDS", "")).split(",")
    if x.strip().isdigit()
}

_channel_raw = _clean(os.getenv("REQUIRED_CHANNEL", "working_moneymo")).lstrip("@")
REQUIRED_CHANNEL = f"@{_channel_raw}" if _channel_raw else ""
CHANNEL_LINK = f"https://t.me/{_channel_raw}" if _channel_raw else ""


def is_admin(telegram_id: int) -> bool:
    return telegram_id in ADMIN_IDS
