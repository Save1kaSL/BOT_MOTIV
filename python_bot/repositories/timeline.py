"""Lead timeline."""

from __future__ import annotations

from db.connection import get_connection
from repositories.base import dumps


def add_event(
    telegram_id: int,
    event_type: str,
    *,
    offer_id: str | None = None,
    user_offer_id: int | None = None,
    title: str | None = None,
    payload: dict | None = None,
) -> int:
    with get_connection() as c:
        cur = c.execute(
            """
            INSERT INTO lead_timeline
            (telegram_id, offer_id, user_offer_id, event_type, title, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                telegram_id,
                offer_id,
                user_offer_id,
                event_type,
                title,
                dumps(payload or {}),
            ),
        )
        c.commit()
        return cur.lastrowid


def list_events(
    telegram_id: int,
    *,
    offer_id: str | None = None,
    limit: int = 30,
    offset: int = 0,
) -> list[dict]:
    where = "WHERE telegram_id = ?"
    params: list = [telegram_id]
    if offer_id:
        where += " AND offer_id = ?"
        params.append(offer_id)
    with get_connection() as c:
        rows = c.execute(
            f"""
            SELECT * FROM lead_timeline {where}
            ORDER BY id DESC LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
    return [dict(r) for r in rows]
