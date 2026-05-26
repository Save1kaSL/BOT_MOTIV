# BOT_MOTIV — Telegram RKO Affiliate Bot

Python 3.11+ · aiogram 3 · SQLite · FSM

## Запуск

```bash
cd /path/to/BOT_MOTIV
cp .env.example .env   # заполнить TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_IDS
./bot.sh
```

Миграции применяются автоматически при старте. Вручную:

```bash
cd python_bot && python scripts/migrate.py
```

## Архитектура

```
python_bot/
├── db/                 # connection, migrations
├── models/             # constants (pipeline, risk, payout types)
├── repositories/       # SQLite data access
├── services/           # business logic
│   ├── lead_scoring.py
│   ├── duplicate_detection.py
│   ├── pipeline.py
│   ├── analytics.py
│   ├── cashflow.py
│   ├── profit.py
│   ├── retention.py
│   ├── reminders.py
│   ├── timeline.py
│   └── hooks.py        # интеграция с handlers (не ломает FSM)
├── handlers/           # Telegram UI
├── middleware/         # activity tracking
├── jobs/               # background scheduler
├── storage.py          # legacy facade (совместимость)
└── data/users.db
```

## Системы

### Lead scoring / anti-fraud
- `trust_score` 0–100, `risk_level`: low | medium | high
- Факторы: возраст ID, username, фото, активность, rejects, duplicates, completion rate
- High risk → 🔴 в админке, предупреждение о быстрых выплатах

### Duplicate detection
- ИНН, телефон, username, повтор банка
- Флаги в `duplicate_flags`, уведомление админам

### Analytics dashboard
- Admin → **📊 Dashboard**: банки, ROI, profit, leads conversion, cashflow
- Кэш `analytics_cache` (10 мин)

### Cashflow
- `payout_logs`: advance, main, pending/scheduled/paid
- Dashboard: bot owes, hold, expected PP, reserve

### Retention
- После одобрения финала: `retention_tracking`, safe period
- По окончании — уведомления user + admin

### Reminders
- Интервалы 24/48/72 ч (шаги, скрины, safe period)
- Фоновая задача каждые 5 мин

### Pipeline (auto)
`new_lead` → `stable_lead` → `cd_in_progress` → `cd_completed` → `under_review` → `approved` → `hold` → `safe_period` → `completed` | `rejected`

Синхронизируется со старыми статусами (`выбран`, `в_обработке`, …).

### Timeline
`lead_timeline` — все события лида. Admin → заявка → **📜 Timeline**.

## Admin UI

- Dashboard, Cashflow, Payouts, Search, High risk filter
- Risk badges на карточке заявки
- Одобрить / Написать на скринах (без изменений FSM)

## Env

| Переменная | Описание |
|------------|----------|
| `TELEGRAM_BOT_TOKEN` | Токен бота |
| `ADMIN_TELEGRAM_IDS` | ID админов через запятую |
| `TELEGRAM_PROXY` | SOCKS5/HTTP прокси (опционально) |
| `LOG_LEVEL` | DEBUG, INFO, WARNING |

## Совместимость

- Старая БД `data/users.db` мигрируется через `ALTER TABLE`
- `storage.py` API сохранён для handlers
- FSM states не изменены (добавлен только `AdminSearch`)
