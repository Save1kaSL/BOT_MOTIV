# BOT MOTIV — Affiliate Telegram Funnel MVP

Production-ready MVP: Telegram-бот для арбитражной/affiliate воронки, CRM, реферальная система, AI-поддержка и админ-панель.

## Стек

| Слой | Технологии |
|------|------------|
| Bot | Node.js, TypeScript, Telegraf |
| API | Express, Prisma |
| DB | PostgreSQL |
| Admin | Next.js 15 |
| AI | OpenRouter / OpenAI |

## Структура

```
BOT_MOTIV/
├── apps/
│   ├── api/          # REST API (CRM, auth, AI, notifications)
│   ├── bot/          # Telegram bot
│   └── admin/        # Next.js admin panel
├── packages/
│   ├── db/           # Prisma schema + client
│   └── shared/       # Types, constants, utils
├── docker-compose.yml
└── railway*.toml     # Railway deploy configs
```

## Быстрый старт (локально)

### 1. Зависимости

```bash
cp .env.example .env
# Заполните TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USERNAME
npm install
```

### 2. PostgreSQL

```bash
docker compose up postgres -d
```

### 3. База данных

```bash
npm run db:push
npm run db:seed
```

### 4. Запуск

```bash
# Все сервисы
npm run dev

# Или по отдельности
npm run dev:api    # http://localhost:3001
npm run dev:bot    # Telegram polling
npm run dev:admin  # http://localhost:3000
```

### 5. Админ-панель

- URL: http://localhost:3000
- Логин: `admin@example.com` / `changeme123` (из `.env`)

## End-to-end flow

1. Пользователь `/start` → приветствие + механика + реферальная ссылка
2. «Офферы» → список офферов (Альфа-РегБиз и др.)
3. Выбор оффера → персональная ссылка + кнопка «Начать шаги»
4. Пошаговый гайд с inline-кнопками
5. Шаг 3 (Альфа) → сбор данных анкеты (ИНН, ФИО, телефон…)
6. CRM фиксирует статус и этап
7. AI-помощник отвечает с учётом контекста оффера и KB
8. Админ меняет статусы лидов, смотрит аналитику, делает рассылку

## Статусы лидов

`NEW` → `OFFER_SELECTED` → `IN_PROGRESS` → `WAITING_MEETING` → `COMPLETED` → `APPROVED` → `PAID` / `REJECTED`

## API endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/login` | Авторизация админа |
| GET | `/health` | Healthcheck |
| * | `/bot/*` | Internal API для бота (x-internal-key) |
| * | `/admin/*` | CRM API (Bearer JWT) |

## Docker (полный стек)

```bash
cp .env.example .env
docker compose up --build
```

## Railway deploy

Создайте 3 сервиса из одного репозитория:

1. **PostgreSQL** — плагин Railway Postgres
2. **API** — `railway.toml`, Dockerfile `apps/api/Dockerfile`
3. **Bot** — `railway.bot.toml`
4. **Admin** — `railway.admin.toml`

### Переменные окружения (все сервисы)

```
DATABASE_URL=postgresql://...
TELEGRAM_BOT_TOKEN=
TELEGRAM_BOT_USERNAME=
JWT_SECRET=
INTERNAL_API_KEY=
OPENROUTER_API_KEY=   # или OPENAI_API_KEY
ADMIN_EMAIL=
ADMIN_PASSWORD=
```

### API сервис

```
API_PORT=3001
```

### Bot сервис

```
API_URL=https://your-api.railway.app
```

### Admin сервис

```
NEXT_PUBLIC_API_URL=https://your-api.railway.app
```

После деплоя API выполните миграцию:

```bash
railway run npm run db:push
railway run npm run db:seed
```

## Безопасность

- Все секреты в `.env`
- Rate limit на API и боте
- JWT для админки
- Internal key для bot→api
- Audit log действий админов
- Helmet + CORS на API

## Seed данные

- 3 оффера (Альфа-РегБиз, Тинькофф, Сбер)
- FAQ и knowledge base
- Шаблоны уведомлений
- Admin user

## Масштабирование

- Bot и API stateless → горизонтальное масштабирование
- Notifications worker в API (cron interval)
- Prisma connection pooling (PgBouncer на Railway)
- Webhook mode для бота при высокой нагрузке

## License

Private / MIT
