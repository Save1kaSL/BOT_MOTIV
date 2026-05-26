"""Админ-панель в Telegram."""

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config import is_admin
from formatters import _money, format_admin_app, format_admin_menu, format_admin_stats
from keyboards import CB_ADM, admin_menu_keyboard, main_reply_keyboard
from offers import get_offer
from formatters_payout import (
    format_approval_advance,
    format_approval_hold,
    format_approval_requisites_prompt,
)
from storage import (
    OFFER_STATUSES,
    credit_hold_on_approval,
    get_application,
    get_stats,
    list_applications,
    list_users,
    update_application_status,
    update_submission_status,
    get_submission,
)
from states import AdminContact, PayoutDetails
from aiogram.fsm.context import FSMContext

router = Router()


def _guard(user_id: int | None) -> bool:
    return user_id is not None and is_admin(user_id)


@router.message(Command("admin"))
@router.message(F.text == "Админ")
async def cmd_admin(message: Message) -> None:
    if not message.from_user or not _guard(message.from_user.id):
        await message.answer("⛔ Нет доступа.")
        return
    await message.answer(
        format_admin_menu(),
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard(),
    )


@router.callback_query(F.data == f"{CB_ADM}menu")
async def adm_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    if callback.message:
        await callback.message.edit_text(
            format_admin_menu(),
            parse_mode="Markdown",
            reply_markup=admin_menu_keyboard(),
        )


@router.callback_query(F.data == f"{CB_ADM}stats")
async def adm_stats(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    if callback.message:
        await callback.message.edit_text(
            format_admin_stats(get_stats()),
            parse_mode="Markdown",
            reply_markup=admin_menu_keyboard(),
        )


@router.callback_query(F.data == f"{CB_ADM}filter")
async def adm_filter(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None):
        return
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = [
        [InlineKeyboardButton(text=s, callback_data=f"{CB_ADM}apps:{s}:0")]
        for s in OFFER_STATUSES
    ]
    rows.append([InlineKeyboardButton(text="Все", callback_data=f"{CB_ADM}apps:all:0")])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=f"{CB_ADM}menu")])
    if callback.message:
        await callback.message.edit_text(
            "🔍 Выбери статус:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}apps:(.+):(\d+)$"))
async def adm_apps(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return

    status_raw, page_s = callback.data.removeprefix(f"{CB_ADM}apps:").split(":")
    page = int(page_s)
    status = None if status_raw == "all" else status_raw

    items, total = list_applications(page=page, status=status)
    pages = max(1, (total + 7) // 8)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    lines = [f"📋 *Заявки* ({total})\n"]
    if status:
        lines.append(f"Статус: _{status}_\n")

    buttons: list[list[InlineKeyboardButton]] = []
    for app in items:
        offer = get_offer(app["offer_id"])
        bank = offer.name if offer else app["offer_id"]
        name = app["first_name"] or app["username"] or str(app["telegram_id"])
        lines.append(f"• {name} | {bank} | {app['status']}")
        buttons.append([
            InlineKeyboardButton(
                text=f"📄 {name[:18]}",
                callback_data=f"{CB_ADM}app:{app['id']}",
            )
        ])

    nav: list[InlineKeyboardButton] = []
    key = status_raw
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{CB_ADM}apps:{key}:{page - 1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{CB_ADM}apps:{key}:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ Админ", callback_data=f"{CB_ADM}menu")])

    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}app:(\d+)$"))
async def adm_app_detail(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return

    app_id = int(callback.data.removeprefix(f"{CB_ADM}app:"))
    from admin_formatters import format_app_card_extended
    from handlers.admin_dashboard import extended_app_keyboard
    from repositories.offers_repo import get_user_offer_by_id

    app = get_user_offer_by_id(app_id) or get_application(app_id)
    if not app or not callback.message:
        await callback.answer("Не найдено", show_alert=True)
        return

    await callback.message.edit_text(
        format_app_card_extended(app),
        parse_mode="Markdown",
        reply_markup=extended_app_keyboard(app_id),
    )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}st:(\d+):(.+)$"))
async def adm_set_status(callback: CallbackQuery) -> None:
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return

    rest = callback.data.removeprefix(f"{CB_ADM}st:")
    app_id_s, status = rest.split(":", 1)
    app_id = int(app_id_s)
    if update_application_status(app_id, status):
        await callback.answer(f"Статус → {status}")
        app = get_application(app_id)
        if app and callback.message:
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            status_rows = [
                [
                    InlineKeyboardButton(text=s, callback_data=f"{CB_ADM}st:{app_id}:{s}")
                    for s in OFFER_STATUSES[i : i + 2]
                ]
                for i in range(0, len(OFFER_STATUSES), 2)
            ]
            status_rows.append([InlineKeyboardButton(text="◀️ К заявкам", callback_data=f"{CB_ADM}apps:all:0")])
            await callback.message.edit_text(
                format_admin_app(app),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=status_rows),
            )
    else:
        await callback.answer("Ошибка", show_alert=True)


@router.callback_query(F.data.regexp(rf"^{CB_ADM}users:(\d+)$"))
async def adm_users(callback: CallbackQuery) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return

    page = int(callback.data.removeprefix(f"{CB_ADM}users:"))
    users, total = list_users(page=page)
    pages = max(1, (total + 9) // 10)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    lines = [f"👥 *Пользователи* ({total})\n"]
    for u in users:
        ip = "ИП да" if u.has_ip else "ИП нет" if u.has_ip is False else "ИП ?"
        name = u.first_name or u.username or str(u.telegram_id)
        lines.append(f"• {name} | {ip} | холд {u.hold_rub}₽")

    buttons: list[list[InlineKeyboardButton]] = []
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"{CB_ADM}users:{page - 1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"{CB_ADM}users:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="◀️ Админ", callback_data=f"{CB_ADM}menu")])

    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}subok:(\d+)$"))
async def adm_sub_approve(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer("Одобрено")
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return

    sub_id = int(callback.data.removeprefix(f"{CB_ADM}subok:"))
    sub = get_submission(sub_id)
    if not sub:
        return

    update_submission_status(sub_id, "одобрено")
    offer = get_offer(sub["offer_id"])
    bank = offer.name if offer else sub["offer_id"]
    admin_note = f"✅ Одобрено: {bank}, пользователь уведомлён"

    from services.hooks import on_admin_approve

    if callback.from_user:
        await on_admin_approve(
            callback.bot,
            callback.from_user.id,
            sub["telegram_id"],
            sub["offer_id"],
            submission_type=sub["submission_type"],
            sub_id=sub_id,
        )

    try:
        if sub["submission_type"] == "final" and offer:
            payout = credit_hold_on_approval(sub["telegram_id"], sub["offer_id"])
            if payout:
                await callback.bot.send_message(
                    sub["telegram_id"],
                    format_approval_hold(offer, payout),
                    parse_mode="Markdown",
                )
                if payout["advance_amount"] > 0:
                    await callback.bot.send_message(
                        sub["telegram_id"],
                        format_approval_advance(offer, payout["advance_amount"]),
                        parse_mode="Markdown",
                    )
                await callback.bot.send_message(
                    sub["telegram_id"],
                    format_approval_requisites_prompt(),
                    parse_mode="Markdown",
                )
                from aiogram.fsm.storage.base import StorageKey

                key = StorageKey(
                    bot_id=callback.bot.id,
                    chat_id=sub["telegram_id"],
                    user_id=sub["telegram_id"],
                )
                ctx = FSMContext(storage=state.storage, key=key)
                await ctx.set_state(PayoutDetails.waiting_requisites)

                if payout["main_credited"]:
                    admin_note += (
                        f"\n🔒 +{_money(payout['main_amount'])} ₽ в холд "
                        f"(итого {_money(payout['hold_total'])} ₽)"
                    )
        else:
            await callback.bot.send_message(
                sub["telegram_id"],
                f"✅ *{bank}* — шаг принят, продолжай выполнение.",
                parse_mode="Markdown",
            )
    except Exception:
        pass

    if callback.message:
        await callback.message.reply(admin_note)


@router.callback_query(F.data.regexp(rf"^{CB_ADM}submsg:(\d+)$"))
async def adm_sub_message(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return

    sub_id = int(callback.data.removeprefix(f"{CB_ADM}submsg:"))
    sub = get_submission(sub_id)
    if not sub:
        return

    await state.set_state(AdminContact.waiting_message_to_user)
    await state.update_data(sub_id=sub_id, user_id=sub["telegram_id"])
    if callback.message:
        await callback.message.answer(
            f"✉️ Напиши сообщение пользователю `{sub['telegram_id']}`.\n"
            "Оно уйдёт от имени бота.",
            parse_mode="Markdown",
        )


@router.callback_query(F.data.regexp(rf"^{CB_ADM}supprep:(\d+)$"))
async def adm_support_reply(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not _guard(callback.from_user.id if callback.from_user else None) or not callback.data:
        return
    user_id = int(callback.data.removeprefix(f"{CB_ADM}supprep:"))
    await state.set_state(AdminContact.waiting_message_to_user)
    await state.update_data(user_id=user_id, sub_id=0)
    if callback.message:
        await callback.message.answer(
            f"✉️ Напиши сообщение пользователю `{user_id}`.\n"
            "Оно уйдёт от имени бота.",
            parse_mode="Markdown",
        )


@router.message(AdminContact.waiting_message_to_user)
async def adm_send_message_to_user(message: Message, state: FSMContext) -> None:
    if not message.from_user or not _guard(message.from_user.id) or not message.text:
        return

    data = await state.get_data()
    user_id = data.get("user_id")

    try:
        await message.bot.send_message(
            user_id,
            f"📩 *Сообщение от поддержки:*\n\n{message.text}\n\n"
            "_Ответь в этот чат, если нужна помощь._",
            parse_mode="Markdown",
        )
        await message.answer("✅ Сообщение отправлено пользователю")
    except Exception:
        await message.answer("❌ Не удалось отправить (пользователь не писал боту?)")

    await state.clear()
