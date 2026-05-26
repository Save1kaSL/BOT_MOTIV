"""Сообщения после одобрения и по выплатам."""

from formatters import _money
from offers import RkoOffer


def format_approval_hold(offer: RkoOffer, payout: dict) -> str:
    bank = offer.name
    if payout["main_credited"]:
        lines = [
            f"✅ *{bank}* — ЦД одобрено!",
            "",
            f"🔒 *Основная выплата* *{_money(payout['main_amount'])} ₽* зачислена в *холд*.",
            f"Баланс в холде: *{_money(payout['hold_total'])} ₽*",
            "",
            "Основная выплата придёт на карту по графику (~14 дн. после ЦД).",
        ]
    elif payout["already_credited"]:
        lines = [
            f"✅ *{bank}* — уже было одобрено ранее.",
            f"🔒 В холде сейчас: *{_money(payout['hold_total'])} ₽*",
        ]
    else:
        lines = [f"✅ *{bank}* — ЦД одобрено!"]
    return "\n".join(lines)


def format_approval_advance(offer: RkoOffer, advance_amount: int) -> str:
    return (
        f"💰 *Аванс {_money(advance_amount)} ₽* по офферу *{offer.name}*\n\n"
        "Для выплаты аванса *обратитесь к админу* — напишите в этот чат или дождитесь сообщения от поддержки."
    )


def format_approval_requisites_prompt() -> str:
    return (
        "📋 *Укажите реквизиты для получения средств*\n\n"
        "Отправьте одним сообщением:\n"
        "▫️ ФИО получателя\n"
        "▫️ Банк\n"
        "▫️ БИК\n"
        "▫️ Номер счёта или карты\n"
        "▫️ Телефон для связи (по желанию)"
    )
