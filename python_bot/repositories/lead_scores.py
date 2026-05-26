"""Lead scores repository."""

from __future__ import annotations

from db.connection import get_connection
from repositories.base import dumps, loads


def upsert_score(
    telegram_id: int,
    trust_score: int,
    risk_level: str,
    suspicious_flags: list[str],
    duplicate_flags: list[str],
    factors: dict,
) -> None:
    flags_s = dumps(suspicious_flags)
    dup_s = dumps(duplicate_flags)
    factors_s = dumps(factors)
    with get_connection() as c:
        c.execute(
            """
            INSERT INTO lead_scores
            (telegram_id, trust_score, risk_level, suspicious_flags, duplicate_flags, factors_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                trust_score = excluded.trust_score,
                risk_level = excluded.risk_level,
                suspicious_flags = excluded.suspicious_flags,
                duplicate_flags = excluded.duplicate_flags,
                factors_json = excluded.factors_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (telegram_id, trust_score, risk_level, flags_s, dup_s, factors_s),
        )
        c.execute(
            """
            UPDATE users SET trust_score = ?, risk_level = ?,
                suspicious_flags = ?, duplicate_flags = ?
            WHERE telegram_id = ?
            """,
            (trust_score, risk_level, flags_s, dup_s, telegram_id),
        )
        c.commit()


def get_score(telegram_id: int) -> dict | None:
    with get_connection() as c:
        r = c.execute(
            "SELECT * FROM lead_scores WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        if not r:
            r = c.execute(
                "SELECT trust_score, risk_level, suspicious_flags, duplicate_flags FROM users WHERE telegram_id = ?",
                (telegram_id,),
            ).fetchone()
    if not r:
        return None
    return {
        "telegram_id": telegram_id,
        "trust_score": r["trust_score"] if "trust_score" in r.keys() else 50,
        "risk_level": r["risk_level"] or "low",
        "suspicious_flags": loads(r["suspicious_flags"], []),
        "duplicate_flags": loads(r["duplicate_flags"], []),
        "factors": loads(r["factors_json"] if "factors_json" in r.keys() else None, {}),
    }
