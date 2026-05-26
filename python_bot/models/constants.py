"""Константы домена."""

from __future__ import annotations

# Pipeline (авто-этапы лида)
PIPELINE_NEW_LEAD = "new_lead"
PIPELINE_STABLE_LEAD = "stable_lead"
PIPELINE_CD_IN_PROGRESS = "cd_in_progress"
PIPELINE_CD_COMPLETED = "cd_completed"
PIPELINE_UNDER_REVIEW = "under_review"
PIPELINE_APPROVED = "approved"
PIPELINE_HOLD = "hold"
PIPELINE_SAFE_PERIOD = "safe_period"
PIPELINE_COMPLETED = "completed"
PIPELINE_REJECTED = "rejected"

PIPELINE_STAGES = (
    PIPELINE_NEW_LEAD,
    PIPELINE_STABLE_LEAD,
    PIPELINE_CD_IN_PROGRESS,
    PIPELINE_CD_COMPLETED,
    PIPELINE_UNDER_REVIEW,
    PIPELINE_APPROVED,
    PIPELINE_HOLD,
    PIPELINE_SAFE_PERIOD,
    PIPELINE_COMPLETED,
    PIPELINE_REJECTED,
)

# Старые статусы (совместимость)
OFFER_STATUSES = (
    "выбран",
    "в_обработке",
    "на_проверке",
    "одобрено",
    "выплачено",
    "отклонено",
)

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"

PAYOUT_ADVANCE = "advance"
PAYOUT_MAIN = "main"
PAYOUT_RETENTION = "retention"  # legacy type in logs

PAYOUT_PENDING = "pending"
PAYOUT_SCHEDULED = "scheduled"
PAYOUT_PAID = "paid"
PAYOUT_CANCELLED = "cancelled"

RETENTION_ACTIVE = "active"
RETENTION_PERIOD = "retention"
RETENTION_SAFE_COMPLETE = "safe_complete"
RETENTION_RISKY = "risky"

REMINDER_STEP = "next_step"
REMINDER_SCREENSHOT = "upload_screenshot"
REMINDER_SAFE_DAYS = "safe_days_left"
REMINDER_DONT_CLOSE = "dont_close_account"
REMINDER_SAFE_ACTIVE = "safe_period_active"
REMINDER_QUICK_30M = "quick_30m"
REMINDER_QUICK_8H = "quick_8h"

REMINDER_INTERVALS_HOURS = (24, 48, 72)

TIMELINE_APPLICATION = "application"
TIMELINE_SCREENSHOT = "screenshot"
TIMELINE_STEP = "step"
TIMELINE_CD = "cd_final"
TIMELINE_PAYOUT = "payout"
TIMELINE_APPROVE = "approve"
TIMELINE_REJECT = "reject"
TIMELINE_ADMIN = "admin_action"
TIMELINE_PIPELINE = "pipeline_change"
TIMELINE_DUPLICATE = "duplicate_detected"
