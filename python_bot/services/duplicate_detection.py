"""Duplicate detection."""

from __future__ import annotations

import json
import logging

from config import ADMIN_IDS
from db.connection import get_connection
from models.constants import TIMELINE_DUPLICATE
from repositories.lead_scores import get_score, upsert_score
from repositories.offers_repo import (
    find_duplicate_inn,
    find_duplicate_phone,
    find_same_bank_offer,
)
from repositories.timeline import add_event
from services.timeline import log_timeline

logger = logging.getLogger(__name__)


def check_duplicates(
    telegram_id: int,
    offer_id: str,
    form_data: dict | None = None,
    username: str | None = None,
) -> list[str]:
    flags: list[str] = []
    fd = form_data or {}

    inn = (fd.get("inn") or "").strip()
    phone = (fd.get("phone") or "").strip()

    if inn:
        for row in find_duplicate_inn(inn, telegram_id):
            flags.append(f"duplicate_inn:{inn}:app#{row['id']}")
    if phone:
        for row in find_duplicate_phone(phone, telegram_id):
            flags.append(f"duplicate_phone:{phone[-4:]}:app#{row['id']}")

    with get_connection() as c:
        dup_tid = c.execute(
            "SELECT telegram_id FROM users WHERE username = ? AND username IS NOT NULL AND telegram_id != ?",
            (username, telegram_id),
        ).fetchall()
        for r in dup_tid:
            flags.append(f"duplicate_username:{username}:uid#{r['telegram_id']}")

        dup_user = c.execute(
            "SELECT COUNT(*) FROM user_offers WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()[0]
        if find_same_bank_offer(telegram_id, offer_id) > 1:
            flags.append(f"repeat_bank:{offer_id}")

    if flags:
        score = get_score(telegram_id) or {}
        upsert_score(
            telegram_id,
            score.get("trust_score", 40),
            "high" if len(flags) >= 2 else score.get("risk_level", "medium"),
            score.get("suspicious_flags", []),
            list(set(score.get("duplicate_flags", []) + flags)),
            score.get("factors", {}),
        )
        log_timeline(
            telegram_id,
            TIMELINE_DUPLICATE,
            offer_id=offer_id,
            title="Обнаружен возможный дубль",
            payload={"flags": flags},
        )
    return flags


async def notify_admin_duplicates(bot, telegram_id: int, flags: list[str], offer_id: str) -> None:
    if not flags:
        return
    text = (
        f"⚠️ *Дубль / fraud alert*\n"
        f"User `{telegram_id}` | оффер `{offer_id}`\n\n"
        + "\n".join(f"▫️ {f}" for f in flags[:8])
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except Exception as e:
            logger.warning("dup notify %s: %s", admin_id, e)
