"""Форматирование админ dashboard."""

from __future__ import annotations

from formatters import _money, format_admin_app


def risk_badge(risk: str) -> str:
    if risk == "high":
        return "🔴 HIGH"
    if risk == "medium":
        return "🟡 MED"
    return "🟢 LOW"


def format_dashboard(data: dict) -> str:
    cf = data.get("cashflow", {})
    leads = data.get("leads", {})
    lines = [
        "📊 *Analytics Dashboard*",
        "",
        "*Cashflow*",
        f"▫️ Бот должен (hold+pending): *{_money(cf.get('bot_owes', 0))} ₽*",
        f"▫️ В холде: *{_money(cf.get('total_hold', 0))} ₽*",
        f"▫️ Выплачено: *{_money(cf.get('total_paid', 0))} ₽*",
        f"▫️ Pending main: *{_money(cf.get('pending_payouts', 0))} ₽*",
        f"▫️ Pending advance: *{_money(cf.get('pending_advances', 0))} ₽*",
        f"▫️ Ожидается от ПП: *{_money(cf.get('expected_pp', 0))} ₽*",
        f"▫️ Reserve: *{_money(cf.get('payout_reserve', 0))} ₽*",
        "",
        "*Leads*",
        f"▫️ Users: *{leads.get('users', 0)}* | conv *{leads.get('conversion_pct', 0)}%*",
        f"▫️ Completion: *{leads.get('completion_pct', 0)}%*",
        f"▫️ Avg trust: *{leads.get('avg_trust_score', 0)}*",
        f"▫️ High risk: *{leads.get('high_risk_count', 0)}*",
        "",
        "*По банкам* (топ):",
    ]
    for b in data.get("banks", [])[:8]:
        lines.append(
            f"▫️ `{b['offer_id']}` apps *{b['total_apps']}* | "
            f"appr *{b['approve_rate']}%* rej *{b['reject_rate']}%* | "
            f"profit *{_money(b.get('profit', 0))} ₽* ROI *{b.get('roi_pct', 0)}%*"
        )
    lines.append("\n_Обновлено из кэша · см. разделы ниже_")
    return "\n".join(lines)


def format_app_card_extended(app: dict) -> str:
    base = format_admin_app(app)
    risk = app.get("risk_level", "low")
    trust = app.get("trust_score", 50)
    pipeline = app.get("pipeline_stage", "—")
    dup = app.get("duplicate_flags") or []
    sus = app.get("suspicious_flags") or []

    extra = [
        "",
        f"🎯 Pipeline: *{pipeline}*",
        f"📈 Trust: *{trust}* {risk_badge(risk)}",
    ]
    if dup:
        extra.append("⚠️ *Дубли:*")
        extra.extend(f"▫️ {f}" for f in dup[:5])
    if sus:
        extra.append("🚩 *Suspicious:*")
        extra.extend(f"▫️ {f}" for f in sus[:5])
    if risk == "high":
        extra.append("\n🔴 *Не рекомендовать быстрые выплаты*")
    return base + "\n".join(extra)


def format_timeline(events: list[dict]) -> str:
    if not events:
        return "📜 Timeline пуст"
    lines = ["📜 *Lead Timeline*", ""]
    for e in events[:15]:
        title = e.get("title") or e.get("event_type")
        lines.append(f"▫️ {e.get('created_at', '')[:16]} — {title}")
    return "\n".join(lines)


def format_cashflow(cf: dict) -> str:
    return (
        "💵 *Cashflow*\n\n"
        f"Бот должен: *{_money(cf.get('bot_owes', 0))} ₽*\n"
        f"Hold: *{_money(cf.get('total_hold', 0))} ₽*\n"
        f"Paid: *{_money(cf.get('total_paid', 0))} ₽*\n"
        f"Pending main: *{_money(cf.get('pending_payouts', 0))} ₽*\n"
        f"Pending advance: *{_money(cf.get('pending_advances', 0))} ₽*\n"
        f"Expected PP: *{_money(cf.get('expected_pp', 0))} ₽*\n"
        f"Reserve: *{_money(cf.get('payout_reserve', 0))} ₽*"
    )


def format_payouts_list(items: list[dict], page: int, total: int) -> str:
    lines = [f"💳 *Payouts* ({total})", ""]
    for p in items:
        name = p.get("first_name") or p.get("username") or p["telegram_id"]
        lines.append(
            f"#{p['id']} {name} | {p['payout_type']} *{_money(p['amount'])} ₽* | {p['status']}"
        )
    return "\n".join(lines)
