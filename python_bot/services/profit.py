"""Profit & ROI per offer."""

from __future__ import annotations

from db.connection import get_connection
from offers import get_offer, list_offers
from repositories.analytics import cache_get, cache_set


def get_offer_revenue(offer_id: str) -> int:
    offer = get_offer(offer_id)
    if not offer:
        return 0
    with get_connection() as c:
        r = c.execute(
            "SELECT revenue_rub FROM offer_financials WHERE offer_id = ?", (offer_id,)
        ).fetchone()
    if r and r["revenue_rub"]:
        return r["revenue_rub"]
    # default: payout * 1.4 + advance
    return int(offer.payout * 1.4) + offer.advance_payout


def set_offer_revenue(offer_id: str, revenue: int) -> None:
    with get_connection() as c:
        c.execute(
            """
            INSERT INTO offer_financials (offer_id, revenue_rub) VALUES (?, ?)
            ON CONFLICT(offer_id) DO UPDATE SET revenue_rub = excluded.revenue_rub, updated_at = CURRENT_TIMESTAMP
            """,
            (offer_id, revenue),
        )
        c.commit()


def record_offer_revenue(telegram_id: int, offer_id: str) -> None:
    rev = get_offer_revenue(offer_id)
    with get_connection() as c:
        c.execute(
            "UPDATE user_offers SET revenue_rub = ? WHERE telegram_id = ? AND offer_id = ?",
            (rev, telegram_id, offer_id),
        )
        c.commit()


def profit_for_offer(offer_id: str) -> dict:
    offer = get_offer(offer_id)
    if not offer:
        return {}
    revenue = get_offer_revenue(offer_id)
    payout = offer.payout + offer.advance_payout
    profit = revenue - payout
    roi = round(profit / payout * 100, 1) if payout else 0
    return {
        "offer_id": offer_id,
        "name": offer.name,
        "revenue": revenue,
        "payout": payout,
        "main_payout": offer.payout,
        "advance": offer.advance_payout,
        "profit": profit,
        "roi_pct": roi,
    }


def all_offers_profit() -> list[dict]:
    cached = cache_get("offers_profit")
    if cached:
        return cached.get("items", [])
    items = [profit_for_offer(o.id) for o in list_offers()]
    cache_set("offers_profit", {"items": items})
    return items
