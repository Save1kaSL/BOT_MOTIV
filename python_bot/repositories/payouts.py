"""Payout logs & cashflow."""

from __future__ import annotations

from db.connection import get_connection


def create_payout_log(
    telegram_id: int,
    offer_id: str,
    payout_type: str,
    amount: int,
    *,
    user_offer_id: int | None = None,
    status: str = "pending",
    scheduled_date: str | None = None,
    notes: str | None = None,
) -> int:
    with get_connection() as c:
        cur = c.execute(
            """
            INSERT INTO payout_logs
            (telegram_id, offer_id, user_offer_id, payout_type, amount, status, requested, scheduled_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (telegram_id, offer_id, user_offer_id, payout_type, amount, status, scheduled_date, notes),
        )
        c.commit()
        return cur.lastrowid


def update_payout_status(payout_id: int, status: str, paid_at: str | None = None) -> None:
    with get_connection() as c:
        if paid_at:
            c.execute(
                "UPDATE payout_logs SET status = ?, paid_at = ? WHERE id = ?",
                (status, paid_at, payout_id),
            )
        else:
            c.execute("UPDATE payout_logs SET status = ? WHERE id = ?", (status, payout_id))
        c.commit()


def list_payouts(
    *,
    status: str | None = None,
    payout_type: str | None = None,
    offer_id: str | None = None,
    page: int = 0,
    limit: int = 10,
) -> tuple[list[dict], int]:
    clauses = []
    params: list = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if payout_type:
        clauses.append("payout_type = ?")
        params.append(payout_type)
    if offer_id:
        clauses.append("offer_id = ?")
        params.append(offer_id)
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    offset = page * limit
    with get_connection() as c:
        total = c.execute(f"SELECT COUNT(*) FROM payout_logs {where}", params).fetchone()[0]
        rows = c.execute(
            f"""
            SELECT pl.*, u.first_name, u.username
            FROM payout_logs pl
            LEFT JOIN users u ON u.telegram_id = pl.telegram_id
            {where}
            ORDER BY pl.id DESC LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
    return [dict(r) for r in rows], total


def cashflow_summary() -> dict:
    with get_connection() as c:
        hold = c.execute("SELECT COALESCE(SUM(hold_rub), 0) FROM users").fetchone()[0]
        paid = c.execute("SELECT COALESCE(SUM(paid_rub), 0) FROM users").fetchone()[0]
        pending_main = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payout_logs WHERE status = 'pending' AND payout_type = 'main'"
        ).fetchone()[0]
        pending_adv = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payout_logs WHERE status = 'pending' AND payout_type = 'advance'"
        ).fetchone()[0]
        expected_pp = c.execute(
            "SELECT COALESCE(SUM(revenue_rub), 0) FROM user_offers WHERE status IN ('одобрено', 'выплачено', 'на_проверке')"
        ).fetchone()[0]
        scheduled = c.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payout_logs WHERE status = 'scheduled'"
        ).fetchone()[0]
    reserve = max(0, int(expected_pp) - int(hold) - int(pending_main) - int(pending_adv))
    return {
        "total_hold": hold,
        "total_paid": paid,
        "pending_payouts": pending_main,
        "pending_advances": pending_adv,
        "expected_pp": expected_pp,
        "scheduled_payouts": scheduled,
        "payout_reserve": reserve,
        "bot_owes": pending_main + pending_adv + hold,
    }
