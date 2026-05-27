"""Тексты на русском."""

from offer_flow import get_step_instruction, is_smz_step
from offers import RkoOffer


def escape_markdown(text: object) -> str:
    """Экранирование для Telegram legacy Markdown."""
    s = "" if text is None else str(text)
    for ch in ("\\", "_", "*", "`", "["):
        s = s.replace(ch, f"\\{ch}")
    return s


_STATUS_LABELS = {
    "выбран": "выбран",
    "в_обработке": "в обработке",
    "на_проверке": "на проверке",
    "одобрено": "одобрено",
    "выплачено": "выплачено",
    "отклонено": "отклонено",
    "new_lead": "новый лид",
    "stable_lead": "стабильный лид",
    "cd_in_progress": "ЦД в работе",
    "cd_completed": "ЦД выполнено",
    "under_review": "на проверке",
    "approved": "одобрено",
    "hold": "холд",
    "safe_period": "защитный период",
    "completed": "завершено",
    "rejected": "отклонено",
}


def format_status(status: str | None) -> str:
    if not status:
        return "—"
    return _STATUS_LABELS.get(status, status.replace("_", " "))


def _money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ")


def _bullets(items: list[str], emoji: str = "▫️") -> str:
    return "\n".join(f"{emoji} {x}" for x in items)


def format_offers_menu() -> str:
    return (
        "🏦 *Офферы РКО*\n\n"
        "Выбери банк — условия, выплаты, инструкция.\n\n"
        "💡 Схема выплат:\n"
        "▫️ *Аванс* — через 7–10 дней (выплата через админа)\n"
        "▫️ *Основная* — ~14 дней после ЦД (в холд после одобрения)"
    )


def format_offer_card(offer: RkoOffer, current_step: int = 0) -> str:
    total = offer.total_potential
    total_steps = len(offer.steps)
    progress_block = ""
    step_detail = ""
    if total_steps:
        progress_block = f"\n📍 *Прогресс:* шаг {min(current_step + 1, total_steps)} из {total_steps}\n"
        if current_step < total_steps:
            progress_block += f"🔹 *{offer.steps[current_step]}*\n"
        if is_smz_step(offer.id, current_step):
            progress_block += "Подтверди статус СМЗ кнопками ниже.\n"
        else:
            progress_block += "После шага — *скриншот* (кроме шага СМЗ).\n"
        step_detail = "\n" + get_step_instruction(offer.id, min(current_step, total_steps - 1)) + "\n"

    return (
        f"🏦 *{offer.name}*\n\n"
        f"📝 {offer.description}\n\n"
        f"💰 *Выплаты*\n"
        f"▫️ Аванс: *{_money(offer.advance_payout)} ₽* (7–10 дн.)\n"
        f"▫️ Основная: *{_money(offer.payout)} ₽* (~14 дн.)\n"
        f"▫️ Всего: *{_money(total)} ₽*\n\n"
        f"⏳ Защитный период: *{offer.safe_period_days} дн.*\n\n"
        f"🎯 *Целевое действие*\n{offer.cda_conditions}\n"
        f"{progress_block}"
        f"{step_detail}\n"
        f"📋 *Все шаги*\n{_bullets(offer.steps, '🔹')}\n\n"
        f"⚠️ *Критично*\n{_bullets(offer.critical_conditions, '❗')}\n\n"
        f"🚫 *Причины отказа*\n{_bullets(offer.reject_reasons, '✖️')}"
    )


def format_step_screenshot_prompt(offer: RkoOffer, step_index: int) -> str:
    step_title = offer.steps[step_index] if step_index < len(offer.steps) else "—"
    detail = get_step_instruction(offer.id, step_index)
    return (
        f"📸 *Шаг {step_index + 1}: {step_title}*\n\n"
        f"{detail}\n\n"
        "Пришли *фото* скриншота подтверждения."
    )


def format_username_prompt(for_cd: bool = False) -> str:
    if for_cd:
        return (
            "📎 *Укажи username для связи*\n\n"
            "Отправь свой @username в Telegram (например `@ivanov`).\n"
            "Без username админ не сможет написать тебе по ЦД."
        )
    return "Отправь свой @username одним сообщением (например `@ivanov`)."


def format_final_collect_prompt(offer: RkoOffer) -> str:
    return (
        f"📸 *Финальное подтверждение ЦД — {offer.name}*\n\n"
        "Пришли скриншоты выполненного целевого действия:\n"
        "▫️ можно несколько фото\n"
        "▫️ когда готов — нажми *«Отправить админу»*\n\n"
        "Админ проверит и при необходимости свяжется с тобой."
    )


def format_form_prompt(offer: RkoOffer) -> str:
    return (
        f"📝 *Заявка: {offer.name}*\n\n"
        "Отправь *одним сообщением*:\n\n"
        "ИНН: \n"
        "ФИО: \n"
        "Телефон: \n"
        "Почта: \n"
        "Город: "
    )


def format_profile(user, offers_rows: list[dict]) -> str:
    ip = "да" if user.has_ip else "нет" if user.has_ip is False else "не указано"
    lines = [
        "👤 *Профиль*",
        "",
        f"🪪 ИП: *{ip}*",
        f"🔒 *В холде (основная):* {_money(user.hold_rub)} ₽",
        f"💸 *Доступно к выводу:* {_money(getattr(user, 'available_to_withdraw_rub', 0))} ₽",
        f"✅ *Выплачено:* {_money(user.paid_rub)} ₽",
        "",
        "*В холде* — основная выплата после одобрения ЦД админом.",
        "*Аванс* — отдельно, выплата через админа после одобрения.",
        "",
    ]
    if offers_rows:
        lines.append("📋 *Ваши заявки:*")
        from offers import get_offer

        for row in offers_rows:
            o = get_offer(row["offer_id"])
            name = o.name if o else row["offer_id"]
            step = row.get("current_step", 0)
            status = format_status(row.get("status"))
            lines.append(
                f"▫️ {escape_markdown(name)} — {escape_markdown(status)} (шаг {step})"
            )
    else:
        lines.append("📋 Заявок пока нет. Нажми *Офферы*.")
    return "\n".join(lines)


def format_admin_menu() -> str:
    return (
        "🔐 *Админ-панель*\n\n"
        "📊 Аналитика — ROI, деньги, конверсия\n"
        "📋 Заявки — фильтры, поиск, риски\n"
        "💳 Выплаты — журнал выплат\n"
        "🔴 High risk — не рекомендовать быстрые выплаты\n"
        "Скрины: Одобрить / Написать"
    )


def format_admin_stats(stats: dict) -> str:
    lines = [
        "📊 *Статистика*\n",
        f"👤 Пользователей: *{stats['users']}*",
        f"📋 Заявок: *{stats['applications']}*",
        f"📸 Скринов на проверке: *{stats.get('submissions', 0)}*",
        f"🔒 Всего в холде: *{_money(stats['hold_total'])} ₽*",
        f"✅ Всего выплачено: *{_money(stats['paid_total'])} ₽*\n",
        "*По статусам:*",
    ]
    for st, cnt in stats.get("by_status", {}).items():
        lines.append(f"▫️ {escape_markdown(format_status(st))}: {cnt}")
    return "\n".join(lines)


def format_admin_app(app: dict) -> str:
    from offers import get_offer

    offer = get_offer(app["offer_id"])
    bank = offer.name if offer else app["offer_id"]
    ip = "да" if app.get("has_ip") else "нет" if app.get("has_ip") is False else "не указано"
    name = app.get("first_name") or app.get("username") or "—"

    lines = [
        f"📄 *Заявка #{app['id']}*\n",
        f"👤 {escape_markdown(name)} (@{escape_markdown(app.get('username') or '—')})",
        f"🆔 Telegram: `{app['telegram_id']}`",
        f"🪪 ИП: {ip}",
        f"🏦 Банк: *{escape_markdown(bank)}*",
        f"📊 Статус: *{escape_markdown(format_status(app.get('status')))}*",
        f"🔒 Холд юзера: {_money(app.get('hold_rub', 0))} ₽",
        f"💸 Доступно к выводу: {_money(app.get('available_to_withdraw_rub', 0))} ₽",
    ]

    fd = app.get("form_data") or {}
    if fd:
        lines.append("\n📝 *Анкета:*")
        labels = {"inn": "ИНН", "full_name": "ФИО", "phone": "Телефон", "email": "Почта", "city": "Город"}
        for k, v in fd.items():
            lines.append(f"▫️ {labels.get(k, k)}: {escape_markdown(v)}")
    else:
        lines.append("\n📝 Анкета не заполнена (оффер по ссылке)")

    lines.append("\n👇 Смени статус кнопками ниже")
    return "\n".join(lines)


def format_onboarding_pick() -> str:
    return (
        "📋 *Что ты уже оформил?*\n\n"
        "Отмечай банки галочками.\n"
        "Чтобы продолжить, нужно выбрать минимум *2 оффера*.\n"
    )
