from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import ADMIN_IDS
from form_parser import (
    is_valid_email,
    is_valid_full_name,
    is_valid_inn,
    is_valid_phone,
    normalize_inn,
    normalize_phone,
)
from formatters import format_offer_card
from keyboards import offer_detail_keyboard, reply_kb_for
from offer_flow import get_flow
from offers import get_offer
from states import ApplicationForm
from storage import add_user_offer, get_progress, set_step

router = Router()


@router.message(ApplicationForm.waiting_inn)
async def on_form_inn(message: Message, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return
    inn = normalize_inn(message.text)
    if not is_valid_inn(inn):
        await message.answer("❌ ИНН некорректный. Введи 10 или 12 цифр.")
        return
    data = await state.get_data()
    form = dict(data.get("form_data", {}))
    form["inn"] = inn
    await state.update_data(form_data=form)
    await state.set_state(ApplicationForm.waiting_full_name)
    await message.answer("Шаг 2/5: введи *ФИО* полностью.", parse_mode="Markdown")


@router.message(ApplicationForm.waiting_full_name)
async def on_form_name(message: Message, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return
    full_name = message.text.strip()
    if not is_valid_full_name(full_name):
        await message.answer("❌ Укажи ФИО минимум из 2 слов.")
        return
    data = await state.get_data()
    form = dict(data.get("form_data", {}))
    form["full_name"] = full_name
    await state.update_data(form_data=form)
    await state.set_state(ApplicationForm.waiting_phone)
    await message.answer("Шаг 3/5: введи *телефон* в формате +7XXXXXXXXXX.", parse_mode="Markdown")


@router.message(ApplicationForm.waiting_phone)
async def on_form_phone(message: Message, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return
    phone = normalize_phone(message.text)
    if not is_valid_phone(phone):
        await message.answer("❌ Телефон некорректный. Пример: +79001234567")
        return
    data = await state.get_data()
    form = dict(data.get("form_data", {}))
    form["phone"] = f"+{phone}"
    await state.update_data(form_data=form)
    await state.set_state(ApplicationForm.waiting_email)
    await message.answer("Шаг 4/5: введи *почту*.", parse_mode="Markdown")


@router.message(ApplicationForm.waiting_email)
async def on_form_email(message: Message, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return
    email = message.text.strip()
    if not is_valid_email(email):
        await message.answer("❌ Почта некорректная. Пример: mail@example.com")
        return
    data = await state.get_data()
    form = dict(data.get("form_data", {}))
    form["email"] = email
    await state.update_data(form_data=form)
    await state.set_state(ApplicationForm.waiting_city)
    await message.answer("Шаг 5/5: введи *город*.", parse_mode="Markdown")


@router.message(ApplicationForm.waiting_city)
async def on_form_city(message: Message, state: FSMContext) -> None:
    if not message.text or not message.from_user:
        return
    city = message.text.strip()
    if len(city) < 2:
        await message.answer("❌ Город слишком короткий.")
        return

    data = await state.get_data()
    offer_id = data.get("offer_id")
    form_data = dict(data.get("form_data", {}))
    form_data["city"] = city
    offer = get_offer(offer_id) if offer_id else None

    if not offer:
        await state.clear()
        await message.answer("Ошибка. Начни с /offers")
        return

    add_user_offer(message.from_user.id, offer_id, form_data)
    admin_text = (
        f"📝 Новая заявка: {offer.name}\n"
        f"👤 User: {message.from_user.first_name or '-'}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"🔗 Username: @{message.from_user.username or '-'}\n\n"
        f"ИНН: {form_data.get('inn', '-')}\n"
        f"ФИО: {form_data.get('full_name', '-')}\n"
        f"Телефон: {form_data.get('phone', '-')}\n"
        f"Почта: {form_data.get('email', '-')}\n"
        f"Город: {form_data.get('city', '-')}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_message(admin_id, admin_text)
        except Exception:
            pass
    from services.hooks import on_application_submitted

    await on_application_submitted(
        message.bot,
        message.from_user.id,
        offer_id,
        form_data,
        message.from_user.username,
    )
    await state.clear()

    flow = get_flow(offer_id)
    if flow.form_at_step is not None:
        set_step(message.from_user.id, offer_id, flow.form_at_step + 1)
    prog = get_progress(message.from_user.id, offer_id)

    await message.answer(
        f"✅ Заявка *{offer.name}* отправлена админу!\n\n"
        "Следуй инструкции на следующем шаге.\n"
        "После ЦД — основная в *холд*, аванс через админа.",
        parse_mode="Markdown",
        reply_markup=reply_kb_for(message.from_user.id),
    )
    await message.answer(
        format_offer_card(offer, prog["current_step"]),
        parse_mode="Markdown",
        reply_markup=offer_detail_keyboard(offer, prog["current_step"], telegram_id=message.from_user.id if message.from_user else None),
    )
