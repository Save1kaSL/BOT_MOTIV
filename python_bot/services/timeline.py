"""Timeline service facade."""

from __future__ import annotations

from repositories.timeline import add_event, list_events


def log_timeline(
    telegram_id: int,
    event_type: str,
    *,
    offer_id: str | None = None,
    user_offer_id: int | None = None,
    title: str | None = None,
    payload: dict | None = None,
) -> int:
    return add_event(
        telegram_id,
        event_type,
        offer_id=offer_id,
        user_offer_id=user_offer_id,
        title=title,
        payload=payload,
    )


def get_lead_timeline(telegram_id: int, offer_id: str | None = None, limit: int = 20) -> list[dict]:
    return list_events(telegram_id, offer_id=offer_id, limit=limit)
