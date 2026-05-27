"""Расширенная админка: analytics, search, cashflow, timeline."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message, FSInputFile

from config import is_admin
from admin_formatters import (
    format_app_card_extended,
    format_cashflow,
    format_dashboard,
    format_payouts_list,
    format_timeline,
    risk_badge,
)
from handlers.admin import _guard
from keyboards import CB_ADM
from offers import list_offers
from repositories.offers_repo import list_applications_filtered
from repositories.payouts import list_payouts
from services.analytics import build_dashboard
from services.cashflow import get_cashflow_dashboard
from services.timeline import get_lead_timeline
from states import AdminFinance, AdminSearch
from storage import (
    DB_PATH,
    adjust_hold_and_available,
    get_user_balances,
    list_payout_requests,
    mark_payout_paid,
    move_hold_to_available,
)

router = Router()


def _back_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Админ", callback_data=f"{CB_ADM}menu")]]
    )


@router.callback_query(F.data == f"{CB_ADM}dashboard")
async def adm_dashboard(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    data = build_dashboard(refresh=True)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"{CB_ADM}dashboard")],
            [InlineKeyboardButton(text="💵 Деньги (cashflow)", callback_data=f"{CB_ADM}cashflow")],
            [InlineKeyboardButton(text="🔍 Поиск", callback_data=f"{CB_ADM}search")],
            [InlineKeyboardButton(text="🔴 High risk", callback_data=f"{CB_ADM}apps:risk:0")],
            [InlineKeyboardButton(text="💳 Выплаты", callback_data=f"{CB_ADM}payouts:0")],
            [InlineKeyboardButton(text="◀️ Меню", callback_data=f"{CB_ADM}menu")],
        ]
    )
    if callback.message:
        await callback.message.edit_text(format_dashboard(data), parse_mode="Markdown", reply_markup=kb)


@router.callback_query(F.data == f"{CB_ADM}cashflow")
async def adm_cashflow(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    cf = get_cashflow_dashboard()
    if callback.message:
        await callback.message.edit_text(
            format_cashflow(cf), parse_mode="Markdown", reply_markup=_back_menu()
        )


def _payout_type_ru(t: str) -> str:
    return {"main": "основная", "advance": "аванс", "retention": "ретеншн"}.get(t, t)


def _payout_status_ru(s: str) -> str:
    return {
        "pending": "в ожидании",
        "scheduled": "запланировано",
        "paid": "выплачено",
        "cancelled": "отменено",
    }.get(s, s)


@router.callback_query(F.data == f"{CB_ADM}search")
async def adm_search_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    await state.set_state(AdminSearch.waiting_query)
    if callback.message:
        await callback.message.answer(
            "🔍 Введи поиск: ID, username, имя, ИНН, телефон",
            reply_markup=_back_menu(),
        )


@router.message(AdminSearch.waiting_query)
async def adm_search_run(message: Message, state: FSMContext) -> None:
    if not message.from_user or not _guard(message.from_user.id) or not message.text:
        return
    await state.clear()
    items, total = list_applications_filtered(search=message.text.strip(), limit=10)
    if not items:
        await message.answer("Ничего не найдено")
        return
    lines = [f"🔍 Найдено: *{total}*", ""]
    buttons = []
    for app in items[:8]:
        from offers import get_offer
        bank = get_offer(app["offer_id"])
        name = bank.name if bank else app["offer_id"]
        lines.append(
            f"• {app['first_name'] or app['username']} | {name} | {risk_badge(app['risk_level'])}"
        )
        buttons.append([
            InlineKeyboardButton(text=f"📄 #{app['id']}", callback_data=f"{CB_ADM}app:{app['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Админ", callback_data=f"{CB_ADM}menu")])
    await message.answer(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}apps:risk:(\d+)$"))
async def adm_high_risk_apps(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    page = int(callback.data.removeprefix(f"{CB_ADM}apps:risk:"))
    items, total = list_applications_filtered(page=page, fraud_only=True, limit=8)
    lines = [f"🔴 *High risk* ({total})", ""]
    buttons = []
    for app in items:
        from offers import get_offer
        o = get_offer(app["offer_id"])
        lines.append(f"• {app['first_name']} | {o.name if o else app['offer_id']} | trust {app['trust_score']}")
        buttons.append([InlineKeyboardButton(text=f"#{app['id']}", callback_data=f"{CB_ADM}app:{app['id']}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{CB_ADM}apps:risk:{page - 1}"))
    if (page + 1) * 8 < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{CB_ADM}apps:risk:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️", callback_data=f"{CB_ADM}menu")])
    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}payouts:(\d+)$"))
async def adm_payouts(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    page = int(callback.data.removeprefix(f"{CB_ADM}payouts:"))
    items, total = list_payouts(page=page, limit=8)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Админ", callback_data=f"{CB_ADM}menu")],
        ]
    )
    if callback.message:
        await callback.message.edit_text(
            format_payouts_list(items, page, total),
            parse_mode="Markdown",
            reply_markup=kb,
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}payreq:(\d+)$"))
async def adm_payout_requests(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    page = int(callback.data.removeprefix(f"{CB_ADM}payreq:"))
    items, total = list_payout_requests(page=page, limit=7)
    lines = [f"💸 *Запросы на выплаты* ({total})", ""]
    buttons: list[list[InlineKeyboardButton]] = []
    for it in items:
        uname = it.get("contact_username") or it.get("username") or "—"
        req = (it.get("payment_details") or "—")
        req_short = req[:60] + ("…" if len(req) > 60 else "")
        lines.append(
            f"#{it['id']} | `{it['telegram_id']}` | @{uname}\n"
            f"Тип: *{_payout_type_ru(it['payout_type'])}* | {_fmt_money(it['amount'])} ₽ | {_payout_status_ru(it['status'])}\n"
            f"Реквизиты: {req_short}\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"✅ Оплатил #{it['id']}", callback_data=f"{CB_ADM}payok:{it['id']}"),
            InlineKeyboardButton(text=f"❌ Не оплатил #{it['id']}", callback_data=f"{CB_ADM}payno:{it['id']}"),
        ])
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{CB_ADM}payreq:{page - 1}"))
    if (page + 1) * 7 < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{CB_ADM}payreq:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ Админ", callback_data=f"{CB_ADM}menu")])
    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines) if lines else "Запросов нет",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}payok:(\d+)$"))
async def adm_pay_ok(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    pid = int(callback.data.removeprefix(f"{CB_ADM}payok:"))
    ok = mark_payout_paid(pid)
    if callback.message:
        await callback.message.answer("✅ Выплата отмечена как оплаченная" if ok else "Не удалось обновить")


@router.callback_query(F.data.regexp(rf"^{CB_ADM}payno:(\d+)$"))
async def adm_pay_no(callback: CallbackQuery) -> None:
    await callback.answer("Оставили в ожидании")


@router.callback_query(F.data == f"{CB_ADM}dbexp")
async def adm_db_export(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    if callback.message:
        await callback.message.answer_document(FSInputFile(str(DB_PATH)), caption="🗄 Экспорт БД users.db")


@router.callback_query(F.data == f"{CB_ADM}holdedit")
async def adm_hold_edit_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    await state.set_state(AdminFinance.waiting_hold_user_id)
    if callback.message:
        await callback.message.answer("Введи Telegram ID пользователя для изменения hold/доступно:")


@router.message(AdminFinance.waiting_hold_user_id)
async def adm_hold_edit_user(message: Message, state: FSMContext) -> None:
    if not message.from_user or not _guard(message.from_user.id) or not message.text:
        return
    if not message.text.strip().isdigit():
        await message.answer("Нужен числовой Telegram ID")
        return
    uid = int(message.text.strip())
    await state.update_data(telegram_id=uid)
    await state.set_state(AdminFinance.waiting_hold_value)
    await message.answer("Введи значения в формате: hold=12000 available=3500")


@router.message(AdminFinance.waiting_hold_value)
async def adm_hold_edit_values(message: Message, state: FSMContext) -> None:
    if not message.from_user or not _guard(message.from_user.id) or not message.text:
        return
    data = await state.get_data()
    uid = data.get("telegram_id")
    text = message.text.strip().lower()
    hold = None
    available = None
    for part in text.split():
        if part.startswith("hold="):
            v = part.split("=", 1)[1]
            if v.isdigit():
                hold = int(v)
        if part.startswith("available="):
            v = part.split("=", 1)[1]
            if v.isdigit():
                available = int(v)
    if hold is None and available is None:
        await message.answer("Не понял значения. Пример: hold=10000 available=2500")
        return
    before = get_user_balances(uid) if uid else None
    adjust_hold_and_available(uid, hold_rub=hold, available_rub=available)
    after = get_user_balances(uid) if uid else None
    await state.clear()
    await message.answer("✅ Балансы пользователя обновлены")

    # Уведомление пользователю о ручной правке баланса
    if before and after:
        b_hold, b_av = before
        a_hold, a_av = after
        if (b_hold, b_av) != (a_hold, a_av):
            def _fmt(v: int) -> str:
                return f"{int(v):,}".replace(",", " ")

            changed = []
            if b_hold != a_hold:
                changed.append(f"🔒 В холде: *{_fmt(b_hold)} ₽* → *{_fmt(a_hold)} ₽*")
            if b_av != a_av:
                changed.append(f"💸 К выводу: *{_fmt(b_av)} ₽* → *{_fmt(a_av)} ₽*")
            text_user = "ℹ️ Админ обновил ваш баланс.\n\n" + "\n".join(changed)
            try:
                await message.bot.send_message(uid, text_user, parse_mode="Markdown")
            except Exception:
                pass


@router.callback_query(F.data.regexp(rf"^{CB_ADM}timeline:(\d+)$"))
async def adm_timeline(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    app_id = int(callback.data.removeprefix(f"{CB_ADM}timeline:"))
    from repositories.offers_repo import get_user_offer_by_id
    app = get_user_offer_by_id(app_id)
    if not app or not callback.message:
        return
    events = get_lead_timeline(app["telegram_id"], app.get("offer_id"))
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Заявка", callback_data=f"{CB_ADM}app:{app_id}")],
        ]
    )
    await callback.message.edit_text(format_timeline(events), parse_mode="Markdown", reply_markup=kb)


def extended_app_keyboard(app_id: int) -> InlineKeyboardMarkup:
    from models.constants import OFFER_STATUSES
    status_rows = [
        [
            InlineKeyboardButton(text=s, callback_data=f"{CB_ADM}st:{app_id}:{s}")
            for s in OFFER_STATUSES[i : i + 2]
        ]
        for i in range(0, len(OFFER_STATUSES), 2)
    ]
    status_rows.insert(0, [
        InlineKeyboardButton(text="📜 Timeline", callback_data=f"{CB_ADM}timeline:{app_id}"),
        InlineKeyboardButton(text="💸 Одобрить к выводу", callback_data=f"{CB_ADM}toavail:{app_id}"),
    ])
    status_rows.append([InlineKeyboardButton(text="◀️ К заявкам", callback_data=f"{CB_ADM}apps:all:0")])
    return InlineKeyboardMarkup(inline_keyboard=status_rows)


def _fmt_money(v: int) -> str:
    return f"{int(v):,}".replace(",", " ")


@router.callback_query(F.data.regexp(rf"^{CB_ADM}toavail:(\d+)$"))
async def adm_to_available(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    app_id = int(callback.data.removeprefix(f"{CB_ADM}toavail:"))
    from storage import get_application
    app = get_application(app_id)
    if not app:
        return
    uid = app["telegram_id"]
    hold = int(app.get("hold_rub") or 0)
    if hold <= 0:
        if callback.message:
            await callback.message.answer("У пользователя hold = 0")
        return
    move_hold_to_available(uid, hold)
    try:
        await callback.bot.send_message(
            uid,
            f"✅ Админ одобрил вывод. Баланс к выводу зачислен: *{_fmt_money(hold)} ₽*",
            parse_mode="Markdown",
        )
    except Exception:
        pass
    if callback.message:
        await callback.message.answer(f"✅ Переведено в доступно: {_fmt_money(hold)} ₽ для `{uid}`", parse_mode="Markdown")
