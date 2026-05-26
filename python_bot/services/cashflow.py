"""Cashflow & payout orchestration."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from models.constants import PAYOUT_ADVANCE, PAYOUT_MAIN, PAYOUT_PENDING, PAYOUT_SCHEDULED
from offers import get_offer
from repositories.payouts import cashflow_summary, create_payout_log
from repositories.offers_repo import get_user_offer_row
from services.profit import record_offer_revenue

logger = logging.getLogger(__name__)


def on_offer_approved(telegram_id: int, offer_id: str) -> dict:
    """Создаёт payout logs и обновляет финансы оффера."""
    offer = get_offer(offer_id)
    if not offer:
        return {}
    row = get_user_offer_row(telegram_id, offer_id)
    uo_id = row["id"] if row else None

    main_due = (datetime.utcnow() + timedelta(days=14)).date().isoformat()
    adv_due = (datetime.utcnow() + timedelta(days=7)).date().isoformat()

    create_payout_log(
        telegram_id, offer_id, PAYOUT_MAIN, offer.payout,
        user_offer_id=uo_id, status=PAYOUT_SCHEDULED, scheduled_date=main_due,
    )
    create_payout_log(
        telegram_id, offer_id, PAYOUT_ADVANCE, offer.advance_payout,
        user_offer_id=uo_id, status=PAYOUT_PENDING, scheduled_date=adv_due,
        notes="Выплата через админа",
    )
    record_offer_revenue(telegram_id, offer_id)
    summary = cashflow_summary()
    logger.info("cashflow on approve %s/%s", telegram_id, offer_id)
    return summary


def get_cashflow_dashboard() -> dict:
    return cashflow_summary()
