"""SQLite: пользователи, офферы, холд, скриншоты."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "users.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(c: sqlite3.Connection) -> None:
    ucols = {r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()}
    if "payment_details" not in ucols:
        c.execute("ALTER TABLE users ADD COLUMN payment_details TEXT")
    if "contact_username" not in ucols:
        c.execute("ALTER TABLE users ADD COLUMN contact_username TEXT")
    if "available_to_withdraw_rub" not in ucols:
        c.execute("ALTER TABLE users ADD COLUMN available_to_withdraw_rub INTEGER DEFAULT 0")

    cols = {r[1] for r in c.execute("PRAGMA table_info(user_offers)").fetchall()}
    if "current_step" not in cols:
        c.execute("ALTER TABLE user_offers ADD COLUMN current_step INTEGER DEFAULT 0")
    if "progress_data" not in cols:
        c.execute("ALTER TABLE user_offers ADD COLUMN progress_data TEXT DEFAULT '{}'")
    if "hold_credited" not in cols:
        c.execute("ALTER TABLE user_offers ADD COLUMN hold_credited INTEGER DEFAULT 0")
    if "lead_sub1" not in cols:
        c.execute("ALTER TABLE user_offers ADD COLUMN lead_sub1 TEXT")


def init_db() -> None:
    from db.migrations import run_migrations

    run_migrations()
    # legacy migrate для старых инстансов
    with _conn() as c:
        _migrate(c)


@dataclass
class User:
    telegram_id: int
    username: str | None
    first_name: str | None
    has_ip: bool | None
    onboarded: bool
    hold_rub: int
    paid_rub: int
    available_to_withdraw_rub: int


OFFER_STATUSES = (
    "выбран",
    "в_обработке",
    "на_проверке",
    "одобрено",
    "выплачено",
    "отклонено",
)


def get_or_create_user(telegram_id: int, username: str | None, first_name: str | None) -> User:
    init_db()
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        if not row:
            c.execute(
                "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
                (telegram_id, username, first_name),
            )
            row = c.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)).fetchone()
        else:
            c.execute(
                "UPDATE users SET username = ?, first_name = ? WHERE telegram_id = ?",
                (username, first_name, telegram_id),
            )
    return _row_to_user(row)


def _row_to_user(row: sqlite3.Row) -> User:
    return User(
        telegram_id=row["telegram_id"],
        username=row["username"],
        first_name=row["first_name"],
        has_ip=None if row["has_ip"] is None else bool(row["has_ip"]),
        onboarded=bool(row["onboarded"]),
        hold_rub=row["hold_rub"] or 0,
        paid_rub=row["paid_rub"] or 0,
        available_to_withdraw_rub=row["available_to_withdraw_rub"] or 0,
    )


def set_has_ip(telegram_id: int, has_ip: bool) -> None:
    with _conn() as c:
        c.execute("UPDATE users SET has_ip = ? WHERE telegram_id = ?", (int(has_ip), telegram_id))


def set_onboarded(telegram_id: int) -> None:
    with _conn() as c:
        c.execute("UPDATE users SET onboarded = 1 WHERE telegram_id = ?", (telegram_id,))


def ensure_user_offer(telegram_id: int, offer_id: str) -> int:
    """Возвращает id записи user_offers."""
    with _conn() as c:
        row = c.execute(
            "SELECT id FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
            (telegram_id, offer_id),
        ).fetchone()
        if row:
            sub1_row = c.execute(
                "SELECT lead_sub1 FROM user_offers WHERE id = ?",
                (row["id"],),
            ).fetchone()
            if sub1_row and not sub1_row["lead_sub1"]:
                now_month = datetime.utcnow().month
                c.execute(
                    "UPDATE user_offers SET lead_sub1 = ? WHERE id = ?",
                    (f"{now_month}-{row['id']}", row["id"]),
                )
            return row["id"]
        cur = c.execute(
            "INSERT INTO user_offers (telegram_id, offer_id, status) VALUES (?, ?, 'в_обработке')",
            (telegram_id, offer_id),
        )
        app_id = cur.lastrowid
        now_month = datetime.utcnow().month
        c.execute(
            "UPDATE user_offers SET lead_sub1 = ? WHERE id = ?",
            (f"{now_month}-{app_id}", app_id),
        )
        return app_id


def get_progress(telegram_id: int, offer_id: str) -> dict:
    ensure_user_offer(telegram_id, offer_id)
    with _conn() as c:
        row = c.execute(
            "SELECT id, current_step, progress_data, status FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
            (telegram_id, offer_id),
        ).fetchone()
    if not row:
        return {"id": 0, "current_step": 0, "progress_data": {}, "status": "в_обработке"}
    return {
        "id": row["id"],
        "current_step": row["current_step"] or 0,
        "progress_data": json.loads(row["progress_data"] or "{}"),
        "status": row["status"],
    }


def save_step_screenshot(telegram_id: int, offer_id: str, step_index: int, file_id: str) -> None:
    prog = get_progress(telegram_id, offer_id)
    data = prog["progress_data"]
    steps = data.get("steps", [])
    steps.append({"step": step_index, "file_id": file_id})
    data["steps"] = steps
    new_step = max(prog["current_step"], step_index + 1)
    with _conn() as c:
        c.execute(
            "UPDATE user_offers SET current_step = ?, progress_data = ? WHERE telegram_id = ? AND offer_id = ?",
            (new_step, json.dumps(data, ensure_ascii=False), telegram_id, offer_id),
        )


def create_submission(
    telegram_id: int,
    offer_id: str,
    submission_type: str,
    file_ids: list[str],
    step_index: int | None = None,
) -> int:
    with _conn() as c:
        cur = c.execute(
            """
            INSERT INTO screenshot_submissions
            (telegram_id, offer_id, submission_type, step_index, file_ids, status)
            VALUES (?, ?, ?, ?, ?, 'на_проверке')
            """,
            (
                telegram_id,
                offer_id,
                submission_type,
                step_index,
                json.dumps(file_ids, ensure_ascii=False),
            ),
        )
        if submission_type == "final":
            c.execute(
                "UPDATE user_offers SET status = 'на_проверке' WHERE telegram_id = ? AND offer_id = ?",
                (telegram_id, offer_id),
            )
        return cur.lastrowid


def get_submission(sub_id: int) -> dict | None:
    with _conn() as c:
        r = c.execute(
            """
            SELECT s.*, u.first_name, u.username
            FROM screenshot_submissions s
            JOIN users u ON u.telegram_id = s.telegram_id
            WHERE s.id = ?
            """,
            (sub_id,),
        ).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "telegram_id": r["telegram_id"],
        "offer_id": r["offer_id"],
        "submission_type": r["submission_type"],
        "step_index": r["step_index"],
        "file_ids": json.loads(r["file_ids"] or "[]"),
        "status": r["status"],
        "first_name": r["first_name"],
        "username": r["username"],
    }


def update_submission_status(sub_id: int, status: str) -> bool:
    with _conn() as c:
        sub = get_submission(sub_id)
        if not sub:
            return False
        c.execute("UPDATE screenshot_submissions SET status = ? WHERE id = ?", (status, sub_id))
        if status == "одобрено":
            c.execute(
                "UPDATE user_offers SET status = 'одобрено' WHERE telegram_id = ? AND offer_id = ?",
                (sub["telegram_id"], sub["offer_id"]),
            )
        elif status == "отклонено":
            c.execute(
                "UPDATE user_offers SET status = 'отклонено' WHERE telegram_id = ? AND offer_id = ?",
                (sub["telegram_id"], sub["offer_id"]),
            )
        return True


def register_offer_selection(telegram_id: int, offer_id: str) -> None:
    app_id = ensure_user_offer(telegram_id, offer_id)
    with _conn() as c:
        c.execute(
            "UPDATE user_offers SET status = 'выбран' WHERE id = ?",
            (app_id,),
        )


def get_offer_sub1(telegram_id: int, offer_id: str) -> str | None:
    row = None
    with _conn() as c:
        row = c.execute(
            "SELECT lead_sub1 FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
            (telegram_id, offer_id),
        ).fetchone()
    if not row:
        return None
    return row["lead_sub1"]


def count_selected_offers(telegram_id: int) -> int:
    with _conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM user_offers WHERE telegram_id = ? AND status = 'выбран'",
            (telegram_id,),
        ).fetchone()[0]


def get_any_offer_id(telegram_id: int) -> str | None:
    with _conn() as c:
        r = c.execute(
            """
            SELECT offer_id
            FROM user_offers
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (telegram_id,),
        ).fetchone()
    return r["offer_id"] if r else None


def create_payout_request(
    telegram_id: int,
    offer_id: str,
    payout_type: str,
    amount: int,
) -> int | None:
    """Создаёт заявку на выплату для админа (pending).
    Баланс меняется только после mark_payout_paid."""
    if not offer_id:
        offer_id = "unknown"
    if amount is None or int(amount) <= 0:
        return None
    with _conn() as c:
        cur = c.execute(
            """
            INSERT INTO payout_logs
            (telegram_id, offer_id, payout_type, amount, status, requested)
            VALUES (?, ?, ?, ?, 'pending', 1)
            """,
            (telegram_id, offer_id, payout_type, int(amount)),
        )
        return cur.lastrowid


def add_user_offer(telegram_id: int, offer_id: str, form_data: dict | None = None) -> None:
    ensure_user_offer(telegram_id, offer_id)
    with _conn() as c:
        c.execute(
            """
            UPDATE user_offers SET form_data = ?, status = 'в_обработке'
            WHERE telegram_id = ? AND offer_id = ?
            """,
            (json.dumps(form_data or {}, ensure_ascii=False), telegram_id, offer_id),
        )


def credit_hold_on_approval(telegram_id: int, offer_id: str) -> dict | None:
    """Основная выплата + бонус → холд. Аванс — отдельно, через админа."""
    from offers import get_offer

    offer = get_offer(offer_id)
    if not offer:
        return None

    main_amount = offer.payout
    advance_amount = offer.advance_payout

    with _conn() as c:
        row = c.execute(
            "SELECT hold_credited FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
            (telegram_id, offer_id),
        ).fetchone()
        if not row:
            ensure_user_offer(telegram_id, offer_id)
            row = c.execute(
                "SELECT hold_credited FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
                (telegram_id, offer_id),
            ).fetchone()

        already = bool(row and row["hold_credited"])
        if not already and main_amount > 0:
            c.execute(
                "UPDATE users SET hold_rub = hold_rub + ? WHERE telegram_id = ?",
                (main_amount, telegram_id),
            )
            c.execute(
                "UPDATE user_offers SET hold_credited = 1 WHERE telegram_id = ? AND offer_id = ?",
                (telegram_id, offer_id),
            )

        user = c.execute(
            "SELECT hold_rub FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()

    return {
        "main_amount": main_amount,
        "advance_amount": advance_amount,
        "main_credited": not already and main_amount > 0,
        "already_credited": already,
        "hold_total": user["hold_rub"] if user else 0,
        "payout": offer.payout,
    }


def set_contact_username(telegram_id: int, username: str) -> None:
    clean = username.strip().lstrip("@")
    with _conn() as c:
        c.execute(
            "UPDATE users SET contact_username = ? WHERE telegram_id = ?",
            (clean, telegram_id),
        )


def get_contact_username(telegram_id: int) -> str | None:
    with _conn() as c:
        r = c.execute(
            "SELECT contact_username, username FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
    if not r:
        return None
    if r["contact_username"]:
        return r["contact_username"]
    return r["username"]


def set_step(telegram_id: int, offer_id: str, step: int) -> None:
    ensure_user_offer(telegram_id, offer_id)
    with _conn() as c:
        c.execute(
            "UPDATE user_offers SET current_step = ? WHERE telegram_id = ? AND offer_id = ?",
            (step, telegram_id, offer_id),
        )


def save_payment_details(telegram_id: int, details: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE users SET payment_details = ? WHERE telegram_id = ?",
            (details.strip(), telegram_id),
        )


def get_payment_details(telegram_id: int) -> str | None:
    with _conn() as c:
        r = c.execute(
            "SELECT payment_details FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
    return (r["payment_details"] if r and r["payment_details"] else None)


def adjust_hold_and_available(telegram_id: int, hold_rub: int | None = None, available_rub: int | None = None) -> None:
    with _conn() as c:
        if hold_rub is not None:
            c.execute(
                "UPDATE users SET hold_rub = ? WHERE telegram_id = ?",
                (max(0, int(hold_rub)), telegram_id),
            )
        if available_rub is not None:
            c.execute(
                "UPDATE users SET available_to_withdraw_rub = ? WHERE telegram_id = ?",
                (max(0, int(available_rub)), telegram_id),
            )


def move_hold_to_available(telegram_id: int, amount: int) -> None:
    amount = max(0, int(amount))
    with _conn() as c:
        row = c.execute(
            "SELECT hold_rub, available_to_withdraw_rub FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        if not row:
            return
        moved = min(row["hold_rub"] or 0, amount)
        c.execute(
            """
            UPDATE users
            SET hold_rub = hold_rub - ?, available_to_withdraw_rub = available_to_withdraw_rub + ?
            WHERE telegram_id = ?
            """,
            (moved, moved, telegram_id),
        )


def list_payout_requests(page: int = 0, limit: int = 10) -> tuple[list[dict], int]:
    offset = page * limit
    with _conn() as c:
        total = c.execute(
            "SELECT COUNT(*) FROM payout_logs WHERE requested = 1 AND status IN ('pending', 'scheduled')"
        ).fetchone()[0]
        rows = c.execute(
            """
            SELECT pl.id, pl.telegram_id, pl.offer_id, pl.payout_type, pl.amount, pl.status, pl.scheduled_date,
                   u.first_name, u.username, u.contact_username, u.payment_details
            FROM payout_logs pl
            JOIN users u ON u.telegram_id = pl.telegram_id
            WHERE pl.requested = 1 AND pl.status IN ('pending', 'scheduled')
            ORDER BY pl.id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows], total


def mark_payout_paid(payout_id: int) -> bool:
    with _conn() as c:
        row = c.execute(
            "SELECT telegram_id, amount, payout_type, status FROM payout_logs WHERE id = ?",
            (payout_id,),
        ).fetchone()
        if not row or row["status"] == "paid":
            return False
        c.execute(
            "UPDATE payout_logs SET status = 'paid', paid_at = CURRENT_TIMESTAMP WHERE id = ?",
            (payout_id,),
        )
        c.execute(
            "UPDATE users SET paid_rub = paid_rub + ?, available_to_withdraw_rub = MAX(available_to_withdraw_rub - ?, 0) WHERE telegram_id = ?",
            (row["amount"], row["amount"], row["telegram_id"]),
        )
        return True


def get_stats() -> dict:
    with _conn() as c:
        users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        apps = c.execute("SELECT COUNT(*) FROM user_offers").fetchone()[0]
        subs = c.execute(
            "SELECT COUNT(*) FROM screenshot_submissions WHERE status = 'на_проверке'"
        ).fetchone()[0]
        by_status = c.execute(
            "SELECT status, COUNT(*) as cnt FROM user_offers GROUP BY status"
        ).fetchall()
        hold = c.execute("SELECT COALESCE(SUM(hold_rub), 0) FROM users").fetchone()[0]
        paid = c.execute("SELECT COALESCE(SUM(paid_rub), 0) FROM users").fetchone()[0]
    return {
        "users": users,
        "applications": apps,
        "submissions": subs,
        "by_status": {r["status"]: r["cnt"] for r in by_status},
        "hold_total": hold,
        "paid_total": paid,
    }


def list_applications(page: int = 0, limit: int = 8, status: str | None = None) -> tuple[list[dict], int]:
    offset = page * limit
    where = "WHERE uo.status = ?" if status else ""
    params: list = [status] if status else []
    with _conn() as c:
        total = c.execute(f"SELECT COUNT(*) FROM user_offers uo {where}", params).fetchone()[0]
        rows = c.execute(
            f"""
            SELECT uo.id, uo.telegram_id, uo.offer_id, uo.status, uo.form_data, uo.current_step,
                   u.first_name, u.username, u.has_ip
            FROM user_offers uo
            JOIN users u ON u.telegram_id = uo.telegram_id
            {where}
            ORDER BY uo.id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "telegram_id": r["telegram_id"],
            "offer_id": r["offer_id"],
            "status": r["status"],
            "form_data": json.loads(r["form_data"] or "{}"),
            "current_step": r["current_step"] or 0,
            "first_name": r["first_name"],
            "username": r["username"],
            "has_ip": r["has_ip"],
        })
    return items, total


def get_application(app_id: int) -> dict | None:
    with _conn() as c:
        r = c.execute(
            """
            SELECT uo.id, uo.telegram_id, uo.offer_id, uo.status, uo.form_data, uo.current_step,
                   uo.progress_data, u.first_name, u.username, u.has_ip, u.hold_rub, u.paid_rub, u.available_to_withdraw_rub
            FROM user_offers uo
            JOIN users u ON u.telegram_id = uo.telegram_id
            WHERE uo.id = ?
            """,
            (app_id,),
        ).fetchone()
    if not r:
        return None
    return {
        "id": r["id"],
        "telegram_id": r["telegram_id"],
        "offer_id": r["offer_id"],
        "status": r["status"],
        "form_data": json.loads(r["form_data"] or "{}"),
        "current_step": r["current_step"] or 0,
        "progress_data": json.loads(r["progress_data"] or "{}"),
        "first_name": r["first_name"],
        "username": r["username"],
        "has_ip": r["has_ip"],
        "hold_rub": r["hold_rub"] or 0,
        "paid_rub": r["paid_rub"] or 0,
        "available_to_withdraw_rub": r["available_to_withdraw_rub"] or 0,
    }


def update_application_status(app_id: int, status: str) -> bool:
    if status not in OFFER_STATUSES:
        return False
    with _conn() as c:
        cur = c.execute("UPDATE user_offers SET status = ? WHERE id = ?", (status, app_id))
        return cur.rowcount > 0


def list_users(page: int = 0, limit: int = 10) -> tuple[list[User], int]:
    offset = page * limit
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        rows = c.execute(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [_row_to_user(r) for r in rows], total


def get_user_offers(telegram_id: int) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT offer_id, status, form_data, current_step FROM user_offers WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchall()
    result = []
    for r in rows:
        result.append({
            "offer_id": r["offer_id"],
            "status": r["status"],
            "form_data": json.loads(r["form_data"] or "{}"),
            "current_step": r["current_step"] or 0,
        })
    return result
