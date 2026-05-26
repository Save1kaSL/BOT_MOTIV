"""Lead scoring & anti-fraud."""

from __future__ import annotations

import logging
import time
from typing import Any

from db.connection import get_connection
from models.constants import RISK_HIGH, RISK_LOW, RISK_MEDIUM
from repositories.lead_scores import get_score, upsert_score

logger = logging.getLogger(__name__)

_last_message_at: dict[int, float] = {}


def record_user_activity(telegram_id: int) -> None:
    now = time.time()
    prev = _last_message_at.get(telegram_id)
    _last_message_at[telegram_id] = now
    with get_connection() as c:
        c.execute(
            "UPDATE users SET last_activity_at = CURRENT_TIMESTAMP, message_count = COALESCE(message_count, 0) + 1 WHERE telegram_id = ?",
            (telegram_id,),
        )
        if prev:
            delta = int(now - prev)
            if delta < 3600:
                row = c.execute(
                    "SELECT avg_response_sec FROM users WHERE telegram_id = ?", (telegram_id,)
                ).fetchone()
                old = row["avg_response_sec"] if row and row["avg_response_sec"] else delta
                avg = (old + delta) // 2
                c.execute(
                    "UPDATE users SET avg_response_sec = ? WHERE telegram_id = ?",
                    (avg, telegram_id),
                )
        c.commit()


def estimate_account_age_score(telegram_id: int) -> int:
    """Эвристика: меньший telegram_id ≈ старше аккаунт."""
    if telegram_id < 100_000_000:
        return 25
    if telegram_id < 500_000_000:
        return 18
    if telegram_id < 2_000_000_000:
        return 10
    if telegram_id < 5_000_000_000:
        return 5
    return 0


async def refresh_telegram_signals(bot: Any, telegram_id: int) -> dict[str, Any]:
    has_photo = False
    try:
        photos = await bot.get_user_profile_photos(telegram_id, limit=1)
        has_photo = photos.total_count > 0
    except Exception as e:
        logger.debug("profile photos %s: %s", telegram_id, e)
    with get_connection() as c:
        c.execute(
            "UPDATE users SET has_photo = ? WHERE telegram_id = ?",
            (int(has_photo), telegram_id),
        )
        c.commit()
    return {"has_photo": has_photo}


def compute_trust_score(telegram_id: int, *, username: str | None = None) -> dict:
    suspicious: list[str] = []
    factors: dict[str, int] = {}
    score = 50

    with get_connection() as c:
        u = c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if not u:
            return {"trust_score": 50, "risk_level": RISK_LOW, "suspicious_flags": [], "factors": {}}

        age_pts = estimate_account_age_score(telegram_id)
        factors["account_age"] = age_pts
        score += age_pts

        if username:
            score += 8
            factors["username"] = 8
        else:
            suspicious.append("no_username")
            score -= 12

        if u["has_photo"]:
            score += 10
            factors["has_photo"] = 10
        elif u["has_photo"] is not None:
            suspicious.append("no_photo")
            score -= 8

        offers_cnt = c.execute(
            "SELECT COUNT(*) FROM user_offers WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()[0]
        if offers_cnt > 5:
            suspicious.append("many_offers")
            score -= 15
            factors["many_offers"] = -15
        elif offers_cnt >= 1:
            score += min(offers_cnt * 3, 12)
            factors["offers"] = min(offers_cnt * 3, 12)

        rejects = c.execute(
            "SELECT COUNT(*) FROM user_offers WHERE telegram_id = ? AND status = 'отклонено'",
            (telegram_id,),
        ).fetchone()[0]
        if rejects:
            suspicious.append("reject_history")
            score -= rejects * 10
            factors["rejects"] = -rejects * 10

        dup_flags = c.execute(
            "SELECT duplicate_flags FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        import json
        dups = json.loads(dup_flags["duplicate_flags"] or "[]") if dup_flags else []
        if dups:
            suspicious.append("duplicate_history")
            score -= len(dups) * 8

        completed = c.execute(
            """
            SELECT COUNT(*) FROM user_offers
            WHERE telegram_id = ? AND pipeline_stage IN ('approved', 'hold', 'safe_period', 'completed')
            """,
            (telegram_id,),
        ).fetchone()[0]
        total = max(offers_cnt, 1)
        completion_rate = completed / total
        factors["completion_rate"] = int(completion_rate * 20)
        score += int(completion_rate * 20)

        msg_cnt = u["message_count"] or 0
        if msg_cnt >= 10:
            score += 5
            factors["activity"] = 5
        elif msg_cnt < 3:
            score -= 5

        avg_resp = u["avg_response_sec"]
        if avg_resp and avg_resp < 120:
            score += 5
            factors["fast_response"] = 5
        elif avg_resp and avg_resp > 3600:
            suspicious.append("slow_response")
            score -= 5

    score = max(0, min(100, score))
    if score >= 70:
        risk = RISK_LOW
    elif score >= 45:
        risk = RISK_MEDIUM
    else:
        risk = RISK_HIGH

    existing = get_score(telegram_id) or {}
    duplicate_flags = existing.get("duplicate_flags", [])

    upsert_score(telegram_id, score, risk, suspicious, duplicate_flags, factors)
    return {
        "trust_score": score,
        "risk_level": risk,
        "suspicious_flags": suspicious,
        "duplicate_flags": duplicate_flags,
        "factors": factors,
    }
