"""Retention tracking."""

from __future__ import annotations

from datetime import datetime, timedelta

from db.connection import get_connection


def start_retention(user_offer_id: int, telegram_id: int, offer_id: str, safe_period_days: int) -> None:
    end = (datetime.utcnow() + timedelta(days=safe_period_days)).isoformat()
    with get_connection() as c:
        c.execute(
            """
            INSERT INTO retention_tracking
            (user_offer_id, telegram_id, offer_id, safe_period_days, retention_status,
             retention_start_at, retention_end_date)
            VALUES (?, ?, ?, ?, 'retention', CURRENT_TIMESTAMP, ?)
            ON CONFLICT(user_offer_id) DO UPDATE SET
                retention_status = 'retention',
                retention_end_date = excluded.retention_end_date
            """,
            (user_offer_id, telegram_id, offer_id, safe_period_days, end),
        )
        c.commit()


def list_due_retention_checks() -> list[dict]:
    with get_connection() as c:
        rows = c.execute(
            """
            SELECT * FROM retention_tracking
            WHERE retention_end_date <= datetime('now')
              AND retention_status = 'retention'
              AND (notified_admin = 0 OR notified_user = 0)
            """
        ).fetchall()
    return [dict(r) for r in rows]


def mark_retention_notified(rt_id: int, *, admin: bool = False, user: bool = False) -> None:
    with get_connection() as c:
        if admin:
            c.execute("UPDATE retention_tracking SET notified_admin = 1 WHERE id = ?", (rt_id,))
        if user:
            c.execute("UPDATE retention_tracking SET notified_user = 1 WHERE id = ?", (rt_id,))
        c.execute(
            "UPDATE retention_tracking SET retention_status = 'safe_complete' WHERE id = ?",
            (rt_id,),
        )
        c.commit()


def update_retention_status(user_offer_id: int, status: str) -> None:
    with get_connection() as c:
        c.execute(
            "UPDATE retention_tracking SET retention_status = ? WHERE user_offer_id = ?",
            (status, user_offer_id),
        )
        c.commit()
