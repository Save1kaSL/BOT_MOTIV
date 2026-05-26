"""Analytics queries & cache."""

from __future__ import annotations

import json
from datetime import datetime

from db.connection import get_connection
from repositories.base import loads


def cache_set(key: str, payload: dict) -> None:
    with get_connection() as c:
        c.execute(
            """
            INSERT INTO analytics_cache (cache_key, payload, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(cache_key) DO UPDATE SET payload = excluded.payload, updated_at = CURRENT_TIMESTAMP
            """,
            (key, json.dumps(payload, ensure_ascii=False)),
        )
        c.commit()


def cache_get(key: str, max_age_minutes: int = 15) -> dict | None:
    with get_connection() as c:
        r = c.execute(
            "SELECT payload, updated_at FROM analytics_cache WHERE cache_key = ?",
            (key,),
        ).fetchone()
    if not r:
        return None
    return loads(r["payload"], {})


def bank_metrics() -> list[dict]:
    with get_connection() as c:
        rows = c.execute(
            """
            SELECT
                uo.offer_id,
                COUNT(*) as total_apps,
                SUM(CASE WHEN uo.status = 'отклонено' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN uo.status = 'одобрено' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN uo.status = 'выплачено' THEN 1 ELSE 0 END) as paid_status,
                SUM(CASE WHEN uo.hold_credited = 1 THEN 1 ELSE 0 END) as hold_count,
                AVG(
                    CASE WHEN uo.approved_at IS NOT NULL
                    THEN julianday(uo.approved_at) - julianday(uo.rowid)
                    ELSE NULL END
                ) as avg_approve_days,
                COALESCE(SUM(uo.revenue_rub), 0) as total_revenue
            FROM user_offers uo
            GROUP BY uo.offer_id
            ORDER BY total_apps DESC
            """
        ).fetchall()
        hold_by_bank = {
            r["offer_id"]: r["hold_sum"]
            for r in c.execute(
                """
                SELECT offer_id, COUNT(*) * 1 as hold_sum
                FROM user_offers WHERE hold_credited = 1 GROUP BY offer_id
                """
            ).fetchall()
        }
    result = []
    for r in rows:
        total = r["total_apps"] or 1
        rej = r["rejected"] or 0
        appr = r["approved"] or 0
        result.append({
            "offer_id": r["offer_id"],
            "total_apps": total,
            "reject_rate": round(rej / total * 100, 1),
            "approve_rate": round(appr / total * 100, 1),
            "approved": appr,
            "rejected": rej,
            "hold_count": r["hold_count"] or 0,
            "total_revenue": r["total_revenue"] or 0,
            "avg_approve_days": round(r["avg_approve_days"] or 0, 1),
        })
    return result


def lead_metrics() -> dict:
    with get_connection() as c:
        users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        onboarded = c.execute("SELECT COUNT(*) FROM users WHERE onboarded = 1").fetchone()[0]
        with_offer = c.execute("SELECT COUNT(DISTINCT telegram_id) FROM user_offers").fetchone()[0]
        completed = c.execute(
            "SELECT COUNT(*) FROM user_offers WHERE pipeline_stage IN ('completed', 'safe_period', 'hold')"
        ).fetchone()[0]
        high_risk = c.execute("SELECT COUNT(*) FROM users WHERE risk_level = 'high'").fetchone()[0]
        avg_trust = c.execute("SELECT AVG(trust_score) FROM users").fetchone()[0] or 50
    conv = round(with_offer / users * 100, 1) if users else 0
    completion = round(completed / max(with_offer, 1) * 100, 1)
    return {
        "users": users,
        "onboarded": onboarded,
        "with_offers": with_offer,
        "conversion_pct": conv,
        "completion_pct": completion,
        "high_risk_count": high_risk,
        "avg_trust_score": round(avg_trust, 1),
    }
