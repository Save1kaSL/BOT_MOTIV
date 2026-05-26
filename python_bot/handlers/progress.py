"""Шаги, скриншоты, подтверждение ЦД."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from formatters import (
    format_final_collect_prompt,
    format_offer_card,
    format_step_screenshot_prompt,
    format_username_prompt,
)
from keyboards import CB_PROG, CB_SMZ, final_screenshots_keyboard, offer_detail_keyboard
from offer_flow import SMZ_GUIDE
from offers import get_offer
from services.cd_request import notify_cd_request
from services.notify import notify_admins_screenshots
from states import StepProgress, UserContact
from storage import create_submission, get_contact_username, get_progress, save_step_screenshot, set_contact_username, set_step

router = Router()


@router.callback_query(F.data.regexp(rf"^{CB_SMZ}(.+):(yes|no)$"))
async def on_smz_answer(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.from_user or not callback.data or not callback.message:
        return

    rest = callback.data.removeprefix(CB_SMZ)
    offer_id, answer = rest.rsplit(":", 1)
    offer = get_offer(offer_id)
    if not offer:
        return

    if answer == "no":
        await callback.message.answer(SMZ_GUIDE, parse_mode="Markdown")
        return

    set_step(callback.from_user.id, offer_id, 1)
    prog = get_progress(callback.from_user.id, offer_id)
    await callback.message.answer(
        "✅ Отлично! Переходим к шагу 2 — данные заявки.",
        parse_mode="Markdown",
    )
    await callback.message.answer(
        format_offer_card(offer, prog["current_step"]),
        parse_mode="Markdown",
        reply_markup=offer_detail_keyboard(offer, prog["current_step"], telegram_id=callback.from_user.id),
    )


@router.callback_query(F.data.regexp(rf"^{CB_PROG}cdreq:(.+)$"))
async def on_cd_request(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.from_user or not callback.data:
        return

    offer_id = callback.data.removeprefix(f"{CB_PROG}cdreq:")
    contact = get_contact_username(callback.from_user.id)
    if not contact and not callback.from_user.username:
        await state.set_state(UserContact.waiting_username_for_cd)
        await state.update_data(offer_id=offer_id)
        if callback.message:
            await callback.message.answer(format_username_prompt(for_cd=True), parse_mode="Markdown")
        return

    if callback.from_user.username and not contact:
        set_contact_username(callback.from_user.id, callback.from_user.username)

    await notify_cd_request(
        callback.bot,
        callback.from_user.id,
        offer_id,
        first_name=callback.from_user.first_name,
        tg_username=callback.from_user.username,
    )
    if callback.message:
        await callback.message.answer(
            "✅ Запрос отправлен админу. Ожидай сообщения в Telegram.",
            parse_mode="Markdown",
        )


@router.message(UserContact.waiting_username_for_cd)
async def on_username_for_cd(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.text:
        return
    raw = message.text.strip().lstrip("@")
    if len(raw) < 3:
        await message.answer("Укажи корректный @username")
        return

    set_contact_username(message.from_user.id, raw)
    data = await state.get_data()
    offer_id = data.get("offer_id", "")
    await state.clear()

    await notify_cd_request(
        message.bot,
        message.from_user.id,
        offer_id,
        first_name=message.from_user.first_name,
        tg_username=raw,
    )
    await message.answer("✅ Username сохранён, запрос на ЦД отправлен админу.")


@router.callback_query(F.data.regexp(rf"^{CB_PROG}step:(.+):(\d+)$"))
async def on_step_done(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.from_user or not callback.data:
        return

    parts = callback.data.removeprefix(f"{CB_PROG}step:").split(":")
    offer_id, step_s = parts[0], parts[1]
    step_index = int(step_s)

    offer = get_offer(offer_id)
    if not offer or step_index >= len(offer.steps):
        return

    from offer_flow import is_smz_step

    if is_smz_step(offer_id, step_index):
        await callback.answer("Сначала подтверди СМЗ кнопками", show_alert=True)
        return

    await state.set_state(StepProgress.waiting_step_screenshot)
    await state.update_data(offer_id=offer_id, step_index=step_index)
    await callback.message.answer(
        format_step_screenshot_prompt(offer, step_index),
        parse_mode="Markdown",
    )


@router.message(StepProgress.waiting_step_screenshot, F.photo)
async def on_step_photo(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.photo:
        return

    data = await state.get_data()
    offer_id = data.get("offer_id")
    step_index = data.get("step_index", 0)
    offer = get_offer(offer_id) if offer_id else None
    if not offer:
        await state.clear()
        return

    file_id = message.photo[-1].file_id
    save_step_screenshot(message.from_user.id, offer_id, step_index, file_id)

    sub_id = create_submission(
        message.from_user.id,
        offer_id,
        "step",
        [file_id],
        step_index=step_index,
    )
    from services.hooks import on_step_screenshot

    await on_step_screenshot(message.from_user.id, offer_id, step_index)
    await notify_admins_screenshots(message.bot, sub_id)

    prog = get_progress(message.from_user.id, offer_id)
    await state.clear()

    if prog["current_step"] < len(offer.steps):
        await message.answer(
            f"✅ Шаг {step_index + 1} принят!\n\nСледующий шаг:",
            parse_mode="Markdown",
        )
        await message.answer(
            format_offer_card(offer, prog["current_step"]),
            parse_mode="Markdown",
            reply_markup=offer_detail_keyboard(offer, prog["current_step"], telegram_id=message.from_user.id),
        )
    else:
        await message.answer(
            "✅ Все шаги с скринами пройдены!\n"
            "Нажми *«ЦД выполнено — финальные скрины»* для отправки на проверку.",
            parse_mode="Markdown",
        )


@router.message(StepProgress.waiting_step_screenshot)
async def on_step_need_photo(message: Message) -> None:
    await message.answer("Нужно *фото* скриншота.", parse_mode="Markdown")


@router.callback_query(F.data.regexp(rf"^{CB_PROG}final:(.+)$"))
async def on_final_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.data or not callback.from_user:
        return

    offer_id = callback.data.removeprefix(f"{CB_PROG}final:")
    offer = get_offer(offer_id)
    if not offer:
        return

    await state.set_state(StepProgress.waiting_final_screenshots)
    await state.update_data(offer_id=offer_id, file_ids=[])
    await callback.message.answer(
        format_final_collect_prompt(offer),
        parse_mode="Markdown",
        reply_markup=final_screenshots_keyboard(offer_id),
    )


@router.message(StepProgress.waiting_final_screenshots, F.photo)
async def on_final_photo(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.photo:
        return

    data = await state.get_data()
    file_ids: list[str] = list(data.get("file_ids", []))
    file_ids.append(message.photo[-1].file_id)
    await state.update_data(file_ids=file_ids)

    await message.answer(
        f"📎 Скрин {len(file_ids)} добавлен.\n"
        "Пришли ещё или нажми *«Отправить админу»*.",
        parse_mode="Markdown",
        reply_markup=final_screenshots_keyboard(data.get("offer_id", "")),
    )


@router.callback_query(F.data.regexp(rf"^{CB_PROG}send:(.+)$"))
async def on_final_send(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.from_user or not callback.data:
        return

    data = await state.get_data()
    offer_id = data.get("offer_id") or callback.data.removeprefix(f"{CB_PROG}send:")
    file_ids: list[str] = data.get("file_ids", [])

    if not file_ids:
        await callback.answer("Сначала пришли хотя бы один скриншот", show_alert=True)
        return

    offer = get_offer(offer_id)
    sub_id = create_submission(callback.from_user.id, offer_id, "final", file_ids)
    from services.hooks import on_final_submission

    await on_final_submission(callback.from_user.id, offer_id)
    await notify_admins_screenshots(callback.bot, sub_id)
    await state.clear()

    bank = offer.name if offer else offer_id
    if callback.message:
        await callback.message.edit_text(
            f"✅ Скриншоты по *{bank}* отправлены на проверку!\n\n"
            "Админ проверит и свяжется с тобой при необходимости.\n"
            "Статус: *на проверке*",
            parse_mode="Markdown",
        )
