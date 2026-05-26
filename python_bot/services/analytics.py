"""Analytics dashboard service."""

from __future__ import annotations

from repositories.analytics import bank_metrics, cache_get, cache_set, lead_metrics
from repositories.payouts import cashflow_summary
from services.profit import all_offers_profit, profit_for_offer


def build_dashboard(*, refresh: bool = False) -> dict:
    if not refresh:
        cached = cache_get("full_dashboard", max_age_minutes=10)
        if cached:
            return cached

    banks = bank_metrics()
    for b in banks:
        p = profit_for_offer(b["offer_id"])
        b["revenue"] = p.get("revenue", 0)
        b["profit"] = p.get("profit", 0)
        b["roi_pct"] = p.get("roi_pct", 0)
        b["total_payout"] = p.get("payout", 0)

    data = {
        "banks": banks,
        "leads": lead_metrics(),
        "cashflow": cashflow_summary(),
        "offers_profit": all_offers_profit(),
    }
    cache_set("full_dashboard", data)
    return data
