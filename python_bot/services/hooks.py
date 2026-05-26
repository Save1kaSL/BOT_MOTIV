"""Центральные хуки — не ломают FSM, вызываются после ключевых действий."""

from __future__ import annotations

import logging
from typing import Any

from models.constants import (
    PIPELINE_CD_IN_PROGRESS,
    PIPELINE_UNDER_REVIEW,
    TIMELINE_APPLICATION,
    TIMELINE_APPROVE,
    TIMELINE_CD,
    TIMELINE_SCREENSHOT,
    TIMELINE_STEP,
)
from repositories.admin_actions import log_action
from services.cashflow import on_offer_approved
from services.duplicate_detection import check_duplicates, notify_admin_duplicates
from services.lead_scoring import compute_trust_score, refresh_telegram_signals
from services.pipeline import advance_pipeline, sync_pipeline_from_state
from services.reminders import schedule_offer_reminders, schedule_quick_reminders, schedule_safe_period_reminders
from services.retention import start_safe_period
from services.timeline import log_timeline

logger = logging.getLogger(__name__)


async def on_user_registered(bot: Any, telegram_id: int, username: str | None) -> None:
    try:
        await refresh_telegram_signals(bot, telegram_id)
        compute_trust_score(telegram_id, username=username)
    except Exception:
        logger.exception("on_user_registered %s", telegram_id)


async def on_application_submitted(
    bot: Any,
    telegram_id: int,
    offer_id: str,
    form_data: dict,
    username: str | None,
) -> None:
    flags = check_duplicates(telegram_id, offer_id, form_data, username)
    if flags:
        await notify_admin_duplicates(bot, telegram_id, flags, offer_id)
    log_timeline(telegram_id, TIMELINE_APPLICATION, offer_id=offer_id, title="Заявка отправлена", payload=form_data)
    advance_pipeline(telegram_id, offer_id, PIPELINE_CD_IN_PROGRESS, reason="form_submitted")
    schedule_offer_reminders(telegram_id, offer_id)
    compute_trust_score(telegram_id, username=username)


async def on_step_screenshot(telegram_id: int, offer_id: str, step_index: int) -> None:
    log_timeline(
        telegram_id, TIMELINE_STEP, offer_id=offer_id,
        title=f"Скрин шага {step_index + 1}", payload={"step": step_index},
    )
    sync_pipeline_from_state(telegram_id, offer_id)
    schedule_quick_reminders(telegram_id, offer_id)


async def on_final_submission(telegram_id: int, offer_id: str) -> None:
    log_timeline(telegram_id, TIMELINE_CD, offer_id=offer_id, title="Финальные скрины отправлены")
    advance_pipeline(telegram_id, offer_id, PIPELINE_UNDER_REVIEW, reason="final_screens")


async def on_admin_approve(
    bot: Any,
    admin_id: int,
    telegram_id: int,
    offer_id: str,
    *,
    submission_type: str,
    sub_id: int,
) -> None:
    log_action(admin_id, "approve", target_type="submission", target_id=sub_id, payload={"type": submission_type})
    if submission_type != "final":
        return
    log_timeline(telegram_id, TIMELINE_APPROVE, offer_id=offer_id, title="ЦД одобрено")
    from repositories.offers_repo import set_approved_at, get_user_offer_row
    from offers import get_offer

    row = get_user_offer_row(telegram_id, offer_id)
    if row:
        set_approved_at(row["id"])
    on_offer_approved(telegram_id, offer_id)
    start_safe_period(telegram_id, offer_id)
    offer = get_offer(offer_id)
    if offer:
        schedule_safe_period_reminders(telegram_id, offer_id, offer.safe_period_days)
    from services.pipeline import advance_pipeline
    from models.constants import PIPELINE_HOLD
    advance_pipeline(telegram_id, offer_id, PIPELINE_HOLD, reason="approved")
    compute_trust_score(telegram_id)
    await refresh_telegram_signals(bot, telegram_id)


def on_admin_reject(admin_id: int, telegram_id: int, offer_id: str, sub_id: int) -> None:
    log_action(admin_id, "reject", target_type="submission", target_id=sub_id)
    from models.constants import PIPELINE_REJECTED, TIMELINE_REJECT
    log_timeline(telegram_id, TIMELINE_REJECT, offer_id=offer_id, title="Отклонено")
    advance_pipeline(telegram_id, offer_id, PIPELINE_REJECTED, reason="rejected")
    compute_trust_score(telegram_id)
