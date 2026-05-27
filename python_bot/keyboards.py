from aiogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from offers import RkoOffer, list_offers

CB_OFFER = "rko:"
CB_MFO = "mfo:"
CB_BACK = "rko:back"
CB_PICK = "pick:"
CB_IP = "ip:"
CB_FORM = "form:"
CB_SKIP = "pick:skip"
CB_PROG = "prog:"
CB_SMZ = "smz:"
CB_SUB = "sub:"
CB_SUB_CHECK = "sub:check"

BOT_COMMANDS = [
    BotCommand(command="offers", description="Офферы — список банков"),
    BotCommand(command="mfo", description="Офферы МФО"),
    BotCommand(command="profile", description="Профиль и выплаты"),
    BotCommand(command="admin", description="Админ-панель"),
    BotCommand(command="menu", description="Главное меню"),
    BotCommand(command="start", description="Старт"),
]

CB_ADM = "adm:"


def link_button(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url, style="success")


def subscription_gate_text() -> str:
    from config import REQUIRED_CHANNEL

    return (
        "📢 *Доступ только для подписчиков*\n\n"
        f"Подпишись на канал {REQUIRED_CHANNEL}, затем нажми *Я подписался*."
    )


def subscription_keyboard() -> InlineKeyboardMarkup:
    from config import CHANNEL_LINK, REQUIRED_CHANNEL

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [link_button(f"📢 Подписаться — {REQUIRED_CHANNEL}", CHANNEL_LINK)],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data=CB_SUB_CHECK)],
        ]
    )


def reply_kb_for(telegram_id: int) -> ReplyKeyboardMarkup:
    from config import is_admin

    return main_reply_keyboard(is_admin=is_admin(telegram_id))


def main_reply_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="Офферы РКО"), KeyboardButton(text="Офферы МФО")],
        [KeyboardButton(text="Профиль")],
        [KeyboardButton(text="Поддержка")],
    ]
    if is_admin:
        rows.append([KeyboardButton(text="Админ")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Аналитика", callback_data=f"{CB_ADM}dashboard")],
            [InlineKeyboardButton(text="📈 Статистика", callback_data=f"{CB_ADM}stats")],
            [InlineKeyboardButton(text="📋 Все заявки", callback_data=f"{CB_ADM}apps:all:0")],
            [
                InlineKeyboardButton(text="🔍 Фильтр", callback_data=f"{CB_ADM}filter"),
                InlineKeyboardButton(text="🔎 Поиск", callback_data=f"{CB_ADM}search"),
            ],
            [
                InlineKeyboardButton(text="💵 Деньги (cashflow)", callback_data=f"{CB_ADM}cashflow"),
                InlineKeyboardButton(text="💳 Выплаты", callback_data=f"{CB_ADM}payouts:0"),
            ],
            [
                InlineKeyboardButton(text="💸 Выплаты (запросы)", callback_data=f"{CB_ADM}payreq:0"),
                InlineKeyboardButton(text="🗄 Выгрузка БД", callback_data=f"{CB_ADM}dbexp"),
            ],
            [InlineKeyboardButton(text="✏️ Изменить hold/доступно", callback_data=f"{CB_ADM}holdedit")],
            [InlineKeyboardButton(text="🔴 High risk", callback_data=f"{CB_ADM}apps:risk:0")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data=f"{CB_ADM}users:0")],
        ]
    )


def ip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, ИП есть", callback_data=f"{CB_IP}yes"),
                InlineKeyboardButton(text="❌ Нет ИП", callback_data=f"{CB_IP}no"),
            ],
        ]
    )


def offers_list_keyboard(prefix: str = CB_OFFER) -> InlineKeyboardMarkup:
    offers = list_offers()
    if prefix == CB_MFO:
        offers = [o for o in offers if getattr(o, "category", "rko") == "mfo"]
    else:
        offers = [o for o in offers if getattr(o, "category", "rko") == "rko"]
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for offer in offers:
        row.append(
            InlineKeyboardButton(
                text=f"🏦 {offer.name} — {offer.total_potential} ₽",
                callback_data=f"{prefix}{offer.id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if prefix == CB_PICK:
        rows.append([InlineKeyboardButton(text="⏭ Пропустить", callback_data=CB_SKIP)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def offers_pick_keyboard(
    telegram_id: int,
    prefix: str = CB_PICK,
    *,
    min_selected: int = 2,
) -> InlineKeyboardMarkup:
    """Клавиатура выбора офферов на онбординге с галочками."""
    from storage import get_user_offers, count_selected_offers

    selected = {
        row["offer_id"]
        for row in get_user_offers(telegram_id)
        if row.get("status") == "выбран"
    }
    selected_count = count_selected_offers(telegram_id)
    offers = list_offers()

    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []

    for offer in offers:
        checked = "✅" if offer.id in selected else "⬜"
        row.append(
            InlineKeyboardButton(
                text=f"{checked} {offer.name} — {offer.total_potential} ₽",
                callback_data=f"{prefix}{offer.id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    if selected_count >= min_selected:
        rows.append([InlineKeyboardButton(text="⏭ Продолжить", callback_data=CB_SKIP)])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def smz_keyboard(offer_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ СМЗ есть", callback_data=f"{CB_SMZ}{offer_id}:yes"),
                InlineKeyboardButton(text="❌ Нет СМЗ", callback_data=f"{CB_SMZ}{offer_id}:no"),
            ],
        ]
    )


def offer_detail_keyboard(offer: RkoOffer, current_step: int = 0) -> InlineKeyboardMarkup:
    return _offer_detail_keyboard(offer, current_step=current_step, telegram_id=None)


def _format_referral_link(base_url: str, sub1: str | None) -> str:
    if not sub1:
        return base_url
    if not base_url:
        return base_url
    if "{sub1}" in base_url:
        url = base_url.replace("{sub1}", sub1)
        # если шаблон кривой и содержит '?sub1' после уже существующего '?', превращаем в '&sub1'
        if url.count("?") > 1:
            url = url.replace("?sub1=", "&sub1=")
        return url
    if "sub1=" in base_url:
        # replace existing sub1
        import re
        return re.sub(r"sub1=[^&]*", f"sub1={sub1}", base_url)
    sep = "&" if "?" in base_url else "?"
    return f"{base_url}{sep}sub1={sub1}"


def offer_detail_keyboard(offer: RkoOffer, current_step: int = 0, telegram_id: int | None = None) -> InlineKeyboardMarkup:
    from offer_flow import is_smz_step, needs_form_at_step, shows_link_at_step
    from storage import get_offer_sub1

    rows: list[list[InlineKeyboardButton]] = []
    total = len(offer.steps)

    if is_smz_step(offer.id, current_step):
        rows.extend(smz_keyboard(offer.id).inline_keyboard)
    else:
        if needs_form_at_step(offer.id, current_step):
            rows.append([
                InlineKeyboardButton(text="📝 Данные заявки", callback_data=f"{CB_FORM}{offer.id}"),
            ])
        if shows_link_at_step(offer.id, current_step) and offer.referral_link:
            rows.append([
                link_button(
                    "🔗 Перейти по ссылке",
                    _format_referral_link(
                        offer.referral_link,
                        get_offer_sub1(telegram_id, offer.id) if telegram_id else None,
                    ),
                ),
            ])
        elif not needs_form_at_step(offer.id, current_step) and offer.referral_link and current_step == 0:
            rows.append([
                link_button(
                    "🔗 Перейти по ссылке",
                    _format_referral_link(
                        offer.referral_link,
                        get_offer_sub1(telegram_id, offer.id) if telegram_id else None,
                    ),
                ),
            ])

        if current_step < total and not is_smz_step(offer.id, current_step):
            rows.append([
                InlineKeyboardButton(
                    text=f"✅ Шаг {current_step + 1} выполнен — скрин",
                    callback_data=f"{CB_PROG}step:{offer.id}:{current_step}",
                ),
            ])

    rows.append([
        InlineKeyboardButton(
            text="📣 Запросить выполнение ЦД",
            callback_data=f"{CB_PROG}cdreq:{offer.id}",
        ),
    ])
    rows.append([
        InlineKeyboardButton(
            text="📸 ЦД выполнено — финальные скрины",
            callback_data=f"{CB_PROG}final:{offer.id}",
        ),
    ])
    rows.append([InlineKeyboardButton(text="◀️ Все офферы", callback_data=CB_BACK)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def final_screenshots_keyboard(offer_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📤 Отправить админу на проверку", callback_data=f"{CB_PROG}send:{offer_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"{CB_OFFER}{offer_id}")],
        ]
    )
