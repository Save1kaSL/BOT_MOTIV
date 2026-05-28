"""User offers repository — расширенные запросы."""

from __future__ import annotations

import json

from db.connection import get_connection
from repositories.base import loads


def get_user_offer_row(telegram_id: int, offer_id: str) -> dict | None:
    with get_connection() as c:
        r = c.execute(
            "SELECT * FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
            (telegram_id, offer_id),
        ).fetchone()
    if not r:
        return None
    d = dict(r)
    d["form_data"] = loads(d.get("form_data"), {})
    d["progress_data"] = loads(d.get("progress_data"), {})
    return d


def get_user_offer_by_id(app_id: int) -> dict | None:
    with get_connection() as c:
        r = c.execute(
            """
            SELECT uo.*, u.username, u.first_name, u.trust_score, u.risk_level,
                   u.suspicious_flags, u.duplicate_flags, u.hold_rub, u.paid_rub
            FROM user_offers uo
            JOIN users u ON u.telegram_id = uo.telegram_id
            WHERE uo.id = ?
            """,
            (app_id,),
        ).fetchone()
    if not r:
        return None
    d = dict(r)
    d["form_data"] = loads(d.get("form_data"), {})
    d["progress_data"] = loads(d.get("progress_data"), {})
    d["suspicious_flags"] = loads(d.get("suspicious_flags"), [])
    d["duplicate_flags"] = loads(d.get("duplicate_flags"), [])
    return d


def set_pipeline(app_id: int, stage: str, legacy_status: str | None = None) -> None:
    with get_connection() as c:
        if legacy_status:
            c.execute(
                "UPDATE user_offers SET pipeline_stage = ?, status = ? WHERE id = ?",
                (stage, legacy_status, app_id),
            )
        else:
            c.execute(
                "UPDATE user_offers SET pipeline_stage = ? WHERE id = ?",
                (stage, app_id),
            )
        c.commit()


def set_approved_at(app_id: int) -> None:
    with get_connection() as c:
        c.execute(
            "UPDATE user_offers SET approved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (app_id,),
        )
        c.commit()


def find_duplicate_inn(inn: str, exclude_tid: int) -> list[dict]:
    if not inn:
        return []
    with get_connection() as c:
        rows = c.execute(
            """
            SELECT uo.id, uo.telegram_id, uo.offer_id, uo.status, uo.form_data
            FROM user_offers uo
            WHERE uo.telegram_id != ? AND uo.form_data LIKE ?
            """,
            (exclude_tid, f'%"inn": "{inn}"%'),
        ).fetchall()
    return [dict(r) for r in rows]


def find_duplicate_phone(phone: str, exclude_tid: int) -> list[dict]:
    if not phone:
        return []
    norm = phone.replace(" ", "").replace("-", "")[-10:]
    with get_connection() as c:
        rows = c.execute(
            """
            SELECT uo.id, uo.telegram_id, uo.offer_id, uo.form_data
            FROM user_offers uo
            WHERE uo.telegram_id != ?
            """,
            (exclude_tid,),
        ).fetchall()
    out = []
    for r in rows:
        fd = loads(r["form_data"], {})
        p = (fd.get("phone") or "").replace(" ", "").replace("-", "")
        if norm and norm in p:
            out.append(dict(r))
    return out


def find_same_bank_offer(telegram_id: int, offer_id: str) -> int:
    with get_connection() as c:
        return c.execute(
            "SELECT COUNT(*) FROM user_offers WHERE telegram_id = ? AND offer_id = ?",
            (telegram_id, offer_id),
        ).fetchone()[0]


def list_applications_filtered(
    *,
    page: int = 0,
    limit: int = 8,
    status: str | None = None,
    offer_id: str | None = None,
    risk_level: str | None = None,
    pipeline: str | None = None,
    search: str | None = None,
    fraud_only: bool = False,
) -> tuple[list[dict], int]:
    clauses = []
    params: list = []
    if status:
        clauses.append("uo.status = ?")
        params.append(status)
    if offer_id:
        clauses.append("uo.offer_id = ?")
        params.append(offer_id)
    if pipeline:
        clauses.append("uo.pipeline_stage = ?")
        params.append(pipeline)
    if risk_level:
        clauses.append("u.risk_level = ?")
        params.append(risk_level)
    if fraud_only:
        clauses.append("u.risk_level = 'high'")
    if search:
        clauses.append(
            "(CAST(uo.telegram_id AS TEXT) LIKE ? OR u.username LIKE ? OR u.first_name LIKE ? OR uo.form_data LIKE ?)"
        )
        q = f"%{search}%"
        params.extend([q, q, q, q])
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    offset = page * limit
    with get_connection() as c:
        total = c.execute(
            f"""
            SELECT COUNT(*) FROM user_offers uo
            JOIN users u ON u.telegram_id = uo.telegram_id
            {where}
            """,
            params,
        ).fetchone()[0]
        rows = c.execute(
            f"""
            SELECT uo.id, uo.telegram_id, uo.offer_id, uo.status, uo.pipeline_stage, uo.lead_sub1,
                   uo.form_data, uo.current_step, uo.approved_at,
                   u.first_name, u.username, u.has_ip, u.trust_score, u.risk_level,
                   u.suspicious_flags, u.duplicate_flags
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
            "lead_sub1": r["lead_sub1"],
            "pipeline_stage": r["pipeline_stage"] or "new_lead",
            "form_data": loads(r["form_data"], {}),
            "current_step": r["current_step"] or 0,
            "approved_at": r["approved_at"],
            "first_name": r["first_name"],
            "username": r["username"],
            "has_ip": r["has_ip"],
            "trust_score": r["trust_score"] or 50,
            "risk_level": r["risk_level"] or "low",
            "suspicious_flags": loads(r["suspicious_flags"], []),
            "duplicate_flags": loads(r["duplicate_flags"], []),
        })
    return items, total
