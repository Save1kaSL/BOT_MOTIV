from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from formatters import format_profile
from keyboards import CB_ADM, reply_kb_for
from storage import create_payout_request, get_any_offer_id, get_or_create_user, get_user_offers
from states import PayoutDetails, UserSupport
from config import ADMIN_IDS
from storage import get_contact_username

router = Router()

CB_PROF = "prof:"


@router.message(Command("profile"))
@router.message(F.text.in_(["Профиль", "профиль"]))
async def cmd_profile(message: Message) -> None:
    u = message.from_user
    if not u:
        return

    user = get_or_create_user(u.id, u.username, u.first_name)
    rows = get_user_offers(u.id)
    buttons: list[list[InlineKeyboardButton]] = []
    if getattr(user, "available_to_withdraw_rub", 0) > 0:
        buttons.append([InlineKeyboardButton(text="💸 Запросить выплату", callback_data=f"{CB_PROF}pay")])
    buttons.append([InlineKeyboardButton(text="🧾 Обновить реквизиты", callback_data=f"{CB_PROF}requisites")])
    buttons.append([InlineKeyboardButton(text="✉️ Поддержка", callback_data=f"{CB_PROF}support")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        format_profile(user, rows),
        parse_mode="Markdown",
        reply_markup=kb,
    )
    await message.answer("Меню 👇", reply_markup=reply_kb_for(u.id))


@router.message(F.text == "Поддержка")
async def prof_support_btn_msg(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    await state.set_state(UserSupport.waiting_message)
    await message.answer(
        "Напиши сообщение в поддержку.\n\nНапример: \"Не открывается оффер\", \"Ошибка в шаге\"…",
        parse_mode="Markdown",
    )


@router.callback_query(F.data == f"{CB_PROF}support")
async def prof_support(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    # Пользователь пишет в поддержку — отправляем текст админам и даём ожидание.
    await state.set_state(UserSupport.waiting_message)
    await callback.message.answer(
        "Напиши сообщение в поддержку.\n\nНапример: \"Не открывается оффер\", \"Ошибка в шаге\"…",
        parse_mode="Markdown",
    )


@router.message(UserSupport.waiting_message)
async def on_support_text(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.text:
        return
    txt = message.text.strip()
    uid = message.from_user.id
    name = message.from_user.first_name or message.from_user.username or str(uid)
    for aid in ADMIN_IDS:
        try:
            await message.bot.send_message(
                aid,
                f"🆘 Поддержка\n\nПользователь: {name} (`{uid}`)\nТекст:\n{txt}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="✉️ Ответить",
                                callback_data=f"{CB_ADM}supprep:{uid}",
                            )
                        ]
                    ]
                ),
            )
        except Exception:
            pass
    await message.answer("✅ Сообщение отправлено в поддержку.")
    await state.clear()


@router.callback_query(F.data == f"{CB_PROF}requisites")
async def prof_requisites(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(PayoutDetails.waiting_requisites)
    await callback.message.answer("Пришли реквизиты одним сообщением: ФИО, Банк, БИК, счёт/карта…")


@router.callback_query(F.data == f"{CB_PROF}pay")
async def prof_pay_pick(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    u = get_or_create_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    amount = getattr(u, "available_to_withdraw_rub", 0)
    if amount <= 0:
        await callback.message.answer("Нет доступного баланса к выводу.")
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💸 Аванс ({amount} ₽)",
                    callback_data=f"{CB_PROF}pay_type:advance",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"💸 Основная ({amount} ₽)",
                    callback_data=f"{CB_PROF}pay_type:main",
                )
            ],
        ]
    )
    await callback.message.answer("Выбери тип выплаты:", reply_markup=kb)


@router.callback_query(F.data.regexp(rf"^{CB_PROF}pay_type:(advance|main)$"))
async def prof_pay_type(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if not callback.from_user or not callback.data:
        return
    payout_type = callback.data.removeprefix(f"{CB_PROF}pay_type:")
    u = get_or_create_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)
    amount = getattr(u, "available_to_withdraw_rub", 0)
    if amount <= 0:
        await callback.message.answer("Баланс к выводу = 0.")
        return
    offer_id = get_any_offer_id(callback.from_user.id) or "unknown"
    req_id = create_payout_request(callback.from_user.id, offer_id, payout_type, amount)
    await callback.message.answer("✅ Заявка на выплату отправлена админам. Ожидай подтверждения.")
    await state.clear()
