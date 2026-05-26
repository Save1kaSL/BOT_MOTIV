"""Admin audit log."""

from __future__ import annotations

from db.connection import get_connection
from repositories.base import dumps


def log_action(
    admin_id: int,
    action_type: str,
    *,
    target_type: str | None = None,
    target_id: int | None = None,
    payload: dict | None = None,
) -> int:
    with get_connection() as c:
        cur = c.execute(
            """
            INSERT INTO admin_actions (admin_id, action_type, target_type, target_id, payload)
            VALUES (?, ?, ?, ?, ?)
            """,
            (admin_id, action_type, target_type, target_id, dumps(payload or {})),
        )
        c.commit()
        return cur.lastrowid
