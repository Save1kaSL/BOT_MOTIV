"""Миграции SQLite — совместимость со старой БД."""

from __future__ import annotations

import logging

from db.connection import get_connection

logger = logging.getLogger(__name__)


def _column_exists(c, table: str, column: str) -> bool:
    cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
    return column in cols


def _migrate_legacy(c) -> None:
    if not _column_exists(c, "users", "payment_details"):
        c.execute("ALTER TABLE users ADD COLUMN payment_details TEXT")
    if not _column_exists(c, "users", "contact_username"):
        c.execute("ALTER TABLE users ADD COLUMN contact_username TEXT")
    if not _column_exists(c, "users", "available_to_withdraw_rub"):
        c.execute("ALTER TABLE users ADD COLUMN available_to_withdraw_rub INTEGER DEFAULT 0")
    if not _column_exists(c, "payout_logs", "requested"):
        c.execute("ALTER TABLE payout_logs ADD COLUMN requested INTEGER DEFAULT 0")
    for col, sql in (
        ("current_step", "ALTER TABLE user_offers ADD COLUMN current_step INTEGER DEFAULT 0"),
        ("progress_data", "ALTER TABLE user_offers ADD COLUMN progress_data TEXT DEFAULT '{}'"),
        ("hold_credited", "ALTER TABLE user_offers ADD COLUMN hold_credited INTEGER DEFAULT 0"),
        ("pipeline_stage", "ALTER TABLE user_offers ADD COLUMN pipeline_stage TEXT DEFAULT 'new_lead'"),
        ("approved_at", "ALTER TABLE user_offers ADD COLUMN approved_at TEXT"),
        ("revenue_rub", "ALTER TABLE user_offers ADD COLUMN revenue_rub INTEGER DEFAULT 0"),
    ):
        if not _column_exists(c, "user_offers", col):
            c.execute(sql)

    ucols = {
        "trust_score": "INTEGER DEFAULT 50",
        "risk_level": "TEXT DEFAULT 'low'",
        "suspicious_flags": "TEXT DEFAULT '[]'",
        "duplicate_flags": "TEXT DEFAULT '[]'",
        "last_activity_at": "TEXT",
        "has_photo": "INTEGER",
        "account_age_score": "INTEGER DEFAULT 0",
        "message_count": "INTEGER DEFAULT 0",
        "avg_response_sec": "INTEGER",
    }
    for col, typedef in ucols.items():
        if not _column_exists(c, "users", col):
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")


def run_migrations() -> None:
    with get_connection() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                has_ip INTEGER,
                onboarded INTEGER DEFAULT 0,
                hold_rub INTEGER DEFAULT 0,
                paid_rub INTEGER DEFAULT 0,
                payment_details TEXT,
                contact_username TEXT,
                available_to_withdraw_rub INTEGER DEFAULT 0,
                trust_score INTEGER DEFAULT 50,
                risk_level TEXT DEFAULT 'low',
                suspicious_flags TEXT DEFAULT '[]',
                duplicate_flags TEXT DEFAULT '[]',
                last_activity_at TEXT,
                has_photo INTEGER,
                account_age_score INTEGER DEFAULT 0,
                message_count INTEGER DEFAULT 0,
                avg_response_sec INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS user_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                offer_id TEXT NOT NULL,
                status TEXT DEFAULT 'в_обработке',
                pipeline_stage TEXT DEFAULT 'new_lead',
                form_data TEXT,
                current_step INTEGER DEFAULT 0,
                progress_data TEXT DEFAULT '{}',
                hold_credited INTEGER DEFAULT 0,
                approved_at TEXT,
                revenue_rub INTEGER DEFAULT 0,
                UNIQUE(telegram_id, offer_id)
            );
            CREATE TABLE IF NOT EXISTS screenshot_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                offer_id TEXT NOT NULL,
                submission_type TEXT NOT NULL,
                step_index INTEGER,
                file_ids TEXT NOT NULL,
                status TEXT DEFAULT 'на_проверке',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS lead_scores (
                telegram_id INTEGER PRIMARY KEY,
                trust_score INTEGER DEFAULT 50,
                risk_level TEXT DEFAULT 'low',
                suspicious_flags TEXT DEFAULT '[]',
                duplicate_flags TEXT DEFAULT '[]',
                factors_json TEXT DEFAULT '{}',
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS payout_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                offer_id TEXT NOT NULL,
                user_offer_id INTEGER,
                payout_type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                requested INTEGER DEFAULT 0,
                scheduled_date TEXT,
                paid_at TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                offer_id TEXT,
                reminder_type TEXT NOT NULL,
                due_at TEXT NOT NULL,
                sent_at TEXT,
                status TEXT DEFAULT 'pending',
                payload TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS retention_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_offer_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                offer_id TEXT NOT NULL,
                safe_period_days INTEGER NOT NULL,
                retention_status TEXT DEFAULT 'active',
                retention_start_at TEXT,
                retention_end_date TEXT,
                notified_admin INTEGER DEFAULT 0,
                notified_user INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_offer_id)
            );
            CREATE TABLE IF NOT EXISTS analytics_cache (
                cache_key TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                target_type TEXT,
                target_id INTEGER,
                payload TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS lead_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                offer_id TEXT,
                user_offer_id INTEGER,
                event_type TEXT NOT NULL,
                title TEXT,
                payload TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS offer_financials (
                offer_id TEXT PRIMARY KEY,
                revenue_rub INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS cashflow_snapshot (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT DEFAULT (date('now')),
                total_hold INTEGER DEFAULT 0,
                total_paid INTEGER DEFAULT 0,
                pending_payouts INTEGER DEFAULT 0,
                pending_advances INTEGER DEFAULT 0,
                expected_pp INTEGER DEFAULT 0,
                reserve INTEGER DEFAULT 0,
                payload TEXT DEFAULT '{}'
            );
        """)
        _migrate_legacy(c)
        for stmt in (
            "CREATE INDEX IF NOT EXISTS idx_user_offers_status ON user_offers(status)",
            "CREATE INDEX IF NOT EXISTS idx_user_offers_pipeline ON user_offers(pipeline_stage)",
            "CREATE INDEX IF NOT EXISTS idx_user_offers_offer ON user_offers(offer_id)",
            "CREATE INDEX IF NOT EXISTS idx_payout_logs_status ON payout_logs(status)",
            "CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_at, status)",
            "CREATE INDEX IF NOT EXISTS idx_timeline_user ON lead_timeline(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_timeline_offer ON lead_timeline(offer_id)",
        ):
            try:
                c.execute(stmt)
            except Exception as e:
                logger.warning("Index skip: %s — %s", stmt[:40], e)
        _seed_offer_financials(c)
        c.commit()
    logger.info("Database migrations applied")


def _seed_offer_financials(c) -> None:
    try:
        from offers import list_offers
    except ImportError:
        return
    for o in list_offers():
        rev = int(o.payout * 1.4) + o.advance_payout
        c.execute(
            """
            INSERT INTO offer_financials (offer_id, revenue_rub) VALUES (?, ?)
            ON CONFLICT(offer_id) DO NOTHING
            """,
            (o.id, rev),
        )
