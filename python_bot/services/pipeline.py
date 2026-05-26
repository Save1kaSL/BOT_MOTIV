"""Auto status pipeline."""

from __future__ import annotations

import logging

from models.constants import (
    PIPELINE_APPROVED,
    PIPELINE_CD_COMPLETED,
    PIPELINE_CD_IN_PROGRESS,
    PIPELINE_COMPLETED,
    PIPELINE_HOLD,
    PIPELINE_NEW_LEAD,
    PIPELINE_REJECTED,
    PIPELINE_SAFE_PERIOD,
    PIPELINE_STABLE_LEAD,
    PIPELINE_UNDER_REVIEW,
    TIMELINE_PIPELINE,
)
from offers import get_offer
from repositories.offers_repo import get_user_offer_row, set_pipeline
from services.timeline import log_timeline

logger = logging.getLogger(__name__)

# Маппинг pipeline → legacy status
PIPELINE_TO_LEGACY = {
    PIPELINE_NEW_LEAD: "выбран",
    PIPELINE_STABLE_LEAD: "в_обработке",
    PIPELINE_CD_IN_PROGRESS: "в_обработке",
    PIPELINE_CD_COMPLETED: "в_обработке",
    PIPELINE_UNDER_REVIEW: "на_проверке",
    PIPELINE_APPROVED: "одобрено",
    PIPELINE_HOLD: "одобрено",
    PIPELINE_SAFE_PERIOD: "одобрено",
    PIPELINE_COMPLETED: "выплачено",
    PIPELINE_REJECTED: "отклонено",
}


def advance_pipeline(
    telegram_id: int,
    offer_id: str,
    stage: str,
    *,
    reason: str | None = None,
) -> None:
    row = get_user_offer_row(telegram_id, offer_id)
    if not row:
        return
    legacy = PIPELINE_TO_LEGACY.get(stage, row.get("status"))
    set_pipeline(row["id"], stage, legacy)
    log_timeline(
        telegram_id,
        TIMELINE_PIPELINE,
        offer_id=offer_id,
        user_offer_id=row["id"],
        title=f"Pipeline → {stage}",
        payload={"reason": reason, "legacy_status": legacy},
    )
    logger.info("pipeline %s/%s -> %s", telegram_id, offer_id, stage)


def sync_pipeline_from_state(telegram_id: int, offer_id: str) -> str:
    row = get_user_offer_row(telegram_id, offer_id)
    if not row:
        advance_pipeline(telegram_id, offer_id, PIPELINE_NEW_LEAD)
        return PIPELINE_NEW_LEAD

    status = row.get("status", "")
    step = row.get("current_step") or 0
    offer = get_offer(offer_id)
    total_steps = len(offer.steps) if offer else 0
    fd = row.get("form_data")

    if status == "отклонено":
        stage = PIPELINE_REJECTED
    elif status == "выплачено":
        stage = PIPELINE_COMPLETED
    elif status == "на_проверке":
        stage = PIPELINE_UNDER_REVIEW
    elif status == "одобрено":
        stage = PIPELINE_HOLD if row.get("hold_credited") else PIPELINE_APPROVED
    elif fd or status == "в_обработке":
        if total_steps and step < total_steps:
            stage = PIPELINE_CD_IN_PROGRESS
        elif total_steps and step >= total_steps:
            stage = PIPELINE_CD_COMPLETED
        else:
            stage = PIPELINE_STABLE_LEAD
    elif status == "выбран":
        stage = PIPELINE_NEW_LEAD
    else:
        stage = PIPELINE_STABLE_LEAD

    set_pipeline(row["id"], stage, PIPELINE_TO_LEGACY.get(stage, status))
    return stage
