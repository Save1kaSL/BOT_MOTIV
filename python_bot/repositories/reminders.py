"""Reminders queue."""

from __future__ import annotations

from datetime import datetime, timedelta

from db.connection import get_connection
from repositories.base import dumps


def schedule_reminder(
    telegram_id: int,
    reminder_type: str,
    hours: int,
    *,
    offer_id: str | None = None,
    payload: dict | None = None,
) -> int:
    # поддержка "0.5 часа" через payload minutes, если передали hours=1 и minutes=30
    if payload and payload.get("minutes") == 30:
        due = (datetime.utcnow() + timedelta(minutes=30)).isoformat()
    else:
        due = (datetime.utcnow() + timedelta(hours=hours)).isoformat()
    with get_connection() as c:
        cur = c.execute(
            """
            INSERT INTO reminders (telegram_id, offer_id, reminder_type, due_at, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_id, offer_id, reminder_type, due, dumps(payload or {})),
        )
        c.commit()
        return cur.lastrowid


def list_due_reminders() -> list[dict]:
    with get_connection() as c:
        rows = c.execute(
            """
            SELECT * FROM reminders
            WHERE status = 'pending' AND due_at <= datetime('now')
            ORDER BY due_at
            LIMIT 50
            """
        ).fetchall()
    return [dict(r) for r in rows]


def mark_sent(reminder_id: int) -> None:
    with get_connection() as c:
        c.execute(
            "UPDATE reminders SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reminder_id,),
        )
        c.commit()
