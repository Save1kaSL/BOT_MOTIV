from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from formatters import format_onboarding_pick, format_offer_card
from keyboards import CB_IP, CB_PICK, CB_SKIP, offers_pick_keyboard, offer_detail_keyboard, reply_kb_for
from offers import get_offer
from storage import count_selected_offers, register_offer_selection, set_has_ip, set_onboarded, toggle_offer_selection

router = Router()


@router.callback_query(F.data.startswith(CB_IP))
async def on_ip_answer(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.from_user or not callback.message:
        return

    has_ip = callback.data == f"{CB_IP}yes"
    set_has_ip(callback.from_user.id, has_ip)

    await state.clear()
    uid = callback.from_user.id

    # Если ИП нет — фиксируем Альфа РегБиз как выбранный и сразу показываем карточку.
    if not has_ip:
        register_offer_selection(uid, "alfa_regbiz")
        offer = get_offer("alfa_regbiz")
        if offer:
            await callback.message.edit_text(
                format_onboarding_pick(),
                parse_mode="Markdown",
                reply_markup=offers_pick_keyboard(uid, prefix=CB_PICK, min_selected=2),
            )
            await callback.message.answer(
                format_offer_card(offer, 0),
                parse_mode="Markdown",
                reply_markup=offer_detail_keyboard(offer, 0, telegram_id=uid),
            )
            return

    await callback.message.edit_text(
        format_onboarding_pick(),
        parse_mode="Markdown",
        reply_markup=offers_pick_keyboard(uid, prefix=CB_PICK, min_selected=2),
    )


@router.callback_query(F.data == CB_SKIP)
async def on_pick_skip(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.from_user or not callback.message:
        return
    uid = callback.from_user.id
    selected = count_selected_offers(uid)
    if selected < 2:
        await callback.answer("Нужно выбрать минимум 2 оффера", show_alert=True)
        return

    set_onboarded(uid)
    await callback.message.edit_text(
        "✅ Онбординг завершён! Можешь выбрать офферы в меню *Офферы*",
        parse_mode="Markdown",
    )
    await callback.message.answer("Меню 👇", reply_markup=reply_kb_for(uid))


@router.callback_query(F.data.startswith(CB_PICK))
async def on_pick_offer(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.from_user or not callback.message or not callback.data:
        return

    offer_id = callback.data.removeprefix(CB_PICK)
    offer = get_offer(offer_id)
    if not offer:
        return

    uid = callback.from_user.id
    toggle_offer_selection(uid, offer_id)

    # Мультивыбор: просто обновляем список с галочками.
    await callback.message.edit_text(
        format_onboarding_pick(),
        parse_mode="Markdown",
        reply_markup=offers_pick_keyboard(uid, prefix=CB_PICK, min_selected=2),
    )
