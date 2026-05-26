from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from formatters import format_form_prompt, format_offer_card, format_offers_menu
from keyboards import CB_BACK, CB_FORM, CB_MFO, CB_OFFER, offer_detail_keyboard, offers_list_keyboard
from offers import get_offer
from states import ApplicationForm
from storage import ensure_user_offer, get_progress
from services.reminders import schedule_quick_reminders

router = Router()


async def show_offers_list(target: Message, *, edit: bool = False) -> None:
    text = format_offers_menu()
    kb = offers_list_keyboard()
    if edit:
        await target.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    else:
        await target.answer(text, parse_mode="Markdown", reply_markup=kb)


@router.message(Command("offers"))
@router.message(F.text.in_(["Офферы РКО", "офферы рко"]))
async def cmd_offers(message: Message) -> None:
    await show_offers_list(message)


@router.message(Command("mfo"))
@router.message(F.text.in_(["Офферы МФО", "офферы мфо"]))
async def cmd_mfo(message: Message) -> None:
    text = "💳 *Офферы МФО*\n\nВыбери МФО — откроется ссылка с sub1.\nДальше — подтверждение скринами через админа."
    await message.answer(text, parse_mode="Markdown", reply_markup=offers_list_keyboard(prefix=CB_MFO))


@router.callback_query(F.data == CB_BACK)
async def on_offers_back(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await show_offers_list(callback.message, edit=True)


@router.callback_query(F.data.startswith(CB_OFFER))
async def on_offer_select(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return

    offer_id = callback.data.removeprefix(CB_OFFER)
    offer = get_offer(offer_id)
    if not offer:
        await callback.answer("Оффер не найден", show_alert=True)
        return

    step = 0
    if callback.from_user:
        ensure_user_offer(callback.from_user.id, offer_id)
        step = get_progress(callback.from_user.id, offer_id)["current_step"]
        schedule_quick_reminders(callback.from_user.id, offer_id)
    await callback.message.edit_text(
        format_offer_card(offer, step),
        parse_mode="Markdown",
        reply_markup=offer_detail_keyboard(offer, step, telegram_id=callback.from_user.id if callback.from_user else None),
    )


@router.callback_query(F.data.startswith(CB_MFO))
async def on_mfo_select(callback: CallbackQuery) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return
    offer_id = callback.data.removeprefix(CB_MFO)
    offer = get_offer(offer_id)
    if not offer:
        await callback.answer("Оффер не найден", show_alert=True)
        return
    step = 0
    if callback.from_user:
        ensure_user_offer(callback.from_user.id, offer_id)
        step = get_progress(callback.from_user.id, offer_id)["current_step"]
        schedule_quick_reminders(callback.from_user.id, offer_id)
    await callback.message.edit_text(
        format_offer_card(offer, step),
        parse_mode="Markdown",
        reply_markup=offer_detail_keyboard(offer, step, telegram_id=callback.from_user.id if callback.from_user else None),
    )


@router.callback_query(F.data.startswith(CB_FORM))
async def on_form_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.data or not callback.message:
        return

    offer_id = callback.data.removeprefix(CB_FORM)
    offer = get_offer(offer_id)
    if not offer:
        return

    from offer_flow import needs_form_at_step

    step = 0
    if callback.from_user:
        step = get_progress(callback.from_user.id, offer_id)["current_step"]
    if not needs_form_at_step(offer_id, step):
        await callback.answer("Анкета доступна на нужном шаге", show_alert=True)
        return

    await state.set_state(ApplicationForm.waiting_inn)
    await state.update_data(offer_id=offer_id, form_data={})
    await callback.message.answer(
        f"📝 *Заявка: {offer.name}*\n\n"
        "Шаг 1/5: введи *ИНН* (10 или 12 цифр):",
        parse_mode="Markdown",
    )
