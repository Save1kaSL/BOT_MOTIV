"""Все офферы РКО."""

from __future__ import annotations

from pydantic import BaseModel, Field

from offer_flow import FORM_OFFER_IDS

SUPPORT_TEXT = (
    "\n\n🆘 При проблемах с выполнением ЦД всегда можете обратиться в поддержку — "
    "мы поможем с активацией."
)


class RkoOffer(BaseModel):
    id: str
    name: str
    payout: int
    advance_payout: int = 500
    safe_period_days: int
    description: str
    cda_conditions: str
    steps: list[str]
    critical_conditions: list[str]
    reject_reasons: list[str]
    referral_link: str = ""
    needs_form: bool = False
    category: str = "rko"

    @property
    def total_potential(self) -> int:
        return self.advance_payout + self.payout


def _offer(
    *,
    id: str,
    name: str,
    payout: int,
    safe_period_days: int,
    description: str,
    cda_conditions: str,
    steps: list[str],
    critical_conditions: list[str],
    reject_reasons: list[str],
    referral_link: str = "",
    advance_payout: int = 500,
    category: str = "rko",
) -> RkoOffer:
    needs_form = id in FORM_OFFER_IDS
    return RkoOffer(
        id=id,
        name=name,
        payout=payout,
        advance_payout=advance_payout,
        safe_period_days=safe_period_days,
        description=description + SUPPORT_TEXT,
        cda_conditions=cda_conditions,
        steps=steps,
        critical_conditions=critical_conditions,
        reject_reasons=reject_reasons,
        referral_link=referral_link,
        needs_form=needs_form,
        category=category,
    )


OFFERS: dict[str, RkoOffer] = {
    "alfa_regbiz": _offer(
        id="alfa_regbiz",
        name="Альфа РегБиз",
        # По прайсу: 3 000 ₽ всего (аванс 500 + основная 2 500)
        payout=2500,
        safe_period_days=30,
        referral_link="https://example.com/alfa-regbiz",
        description="Регистрация ИП и РКО в Альфа-Банке для самозанятых.",
        cda_conditions="Открытие ИП, прохождение анкеты, встреча с банком.",
        steps=[
            "Проверка самозанятости (СМЗ)",
            "Данные заявки, инструкция и ссылка",
            "Письма Альфы и назначение встречи",
            "Письмо ФНС и логин/пароль Альфы",
            "Целевое действие и выплата",
        ],
        critical_conditions=[
            "Данные анкеты — только реальные",
            "Не пропускать звонок банка",
        ],
        reject_reasons=["Дубль", "Неверные данные", "Раннее закрытие счёта"],
    ),
    "alfa_rko": _offer(
        id="alfa_rko",
        name="Альфа РКО",
        # По прайсу: 3 000 ₽ всего (аванс 500 + основная 2 500)
        payout=2500,
        safe_period_days=30,
        referral_link="https://example.com/alfa-rko",
        description="Открытие расчётного счёта в Альфа-Банке.",
        cda_conditions="Активация РКО и выполнение условий банка.",
        steps=[
            "Данные заявки, инструкция и ссылка",
            "Целевое действие и выплата",
        ],
        critical_conditions=["Один ИНН — одна заявка", "Свой номер телефона"],
        reject_reasons=["Дубль", "115-ФЗ"],
    ),
    "vtb": _offer(
        id="vtb",
        name="ВТБ",
        # По прайсу: 2 500 ₽ всего (аванс 500 + основная 2 000)
        payout=2000,
        safe_period_days=30,
        referral_link="https://example.com/vtb-rko",
        description="РКО ВТБ для ИП и ООО.",
        cda_conditions="Остаток на счёте от 5 000 ₽ минимум 1 день.",
        steps=[
            "Данные для заявки и инструкция",
            "Целевое действие (ЦД)",
        ],
        critical_conditions=[
            "Отвечать на звонок банка",
            "Не идти в офис до звонка",
            "Не больше 2 заявок на человека",
        ],
        reject_reasons=["Дубль", "Чужой номер", "Быстрое закрытие"],
    ),
    "tinkoff": _offer(
        id="tinkoff",
        name="Тинькофф",
        # По прайсу: 1 500 ₽ всего (аванс 500 + основная 1 000)
        payout=1000,
        safe_period_days=30,
        referral_link="https://www.tbank.ru/business/rko/",
        description="Тинькофф Бизнес — открытие РКО.",
        cda_conditions="Открытие расчётного счёта.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Бизнесу > 30 дней", "Один ИНН = одна заявка"],
        reject_reasons=["115-ФЗ", "Бизнес < 30 дней", "Закрытие счёта"],
    ),
    "kontur": _offer(
        id="kontur",
        name="Контур",
        payout=5500,
        safe_period_days=60,
        referral_link="https://kontur.ru/bank",
        description="Контур.Банк — платежи или остаток.",
        cda_conditions="3 платежа от 30 000 ₽ или остаток > 10 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Не затирать реф-метки", "Новое ООО — через 3–4 дня"],
        reject_reasons=["ЗСК", "115-ФЗ", "Затёртые метки"],
    ),
    "loko": _offer(
        id="loko",
        name="Локо",
        # По прайсу: 2 500 ₽ всего (аванс 500 + основная 2 000)
        payout=2000,
        safe_period_days=45,
        referral_link="https://rko-group.ru/s/ZJWmXohL",
        description="Локо-Банк — операции между юрлицами.",
        cda_conditions="1 операция от 10 000 ₽ или снятие 100 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Только переводы ИП/ООО", "Не переводить себе"],
        reject_reasons=["Закрытие < 30 дней", "Неуникальный клиент"],
    ),
    "tochka": _offer(
        id="tochka",
        name="Точка",
        payout=4000,
        safe_period_days=30,
        referral_link="https://tochka.com/rko/",
        description="Точка — 4 операции от 16к.",
        cda_conditions="4 операции от 16 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Не физлицам", "Не себе"],
        reject_reasons=["Подозрительные операции"],
    ),
    "sovkom": _offer(
        id="sovkom",
        name="Совкомбанк",
        payout=3500,
        safe_period_days=30,
        referral_link="https://example.com/sovkom",
        description="Совкомбанк — пополнение от 2к.",
        cda_conditions="Пополнение от 2 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Без активной Халвы", "Активность на счёте"],
        reject_reasons=["Есть Халва", "Нет активности"],
    ),
    "ozon": _offer(
        id="ozon",
        name="Ozon",
        # По прайсу: 2 500 ₽ всего (аванс 500 + основная 2 000)
        payout=2000,
        safe_period_days=30,
        referral_link="https://rko-group.ru/s/8azLeKbJ",
        description="Ozon Банк для бизнеса.",
        cda_conditions="Пополнение от 3 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Живые обороты", "Остаток на счёте"],
        reject_reasons=["Спящий счёт", "Накрутка"],
    ),
    "cifra": _offer(
        id="cifra",
        name="Цифра Банк",
        # По прайсу: 2 000 ₽ всего (аванс 500 + основная 1 500)
        payout=1500,
        safe_period_days=30,
        referral_link="https://rko-group.ru/s/yr3V1nwt",
        description="Цифра — оплата тарифа.",
        cda_conditions="Оплата тарифа (не «Быстрый старт»).",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Не тариф Быстрый старт", "Подписать ПД"],
        reject_reasons=["Нет согласия", "Закрытие < 30 дней"],
    ),
    "svoy": _offer(
        id="svoy",
        name="Свой Банк",
        # По прайсу: 2 000 ₽ всего (аванс 500 + основная 1 500)
        payout=1500,
        safe_period_days=30,
        referral_link="https://rko-group.ru/s/ub6qvums",
        description="Свой Банк — 3 операции от 20к.",
        cda_conditions="3 операции от 20 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Без внутренних переводов"],
        reject_reasons=["Клиент уже был", "Закрытие"],
    ),
    "bspb": _offer(
        id="bspb",
        name="БСПБ",
        # По прайсу: 2 000 ₽ всего (аванс 500 + основная 1 500)
        payout=1500,
        safe_period_days=30,
        referral_link="https://rko-group.ru/s/SqMOH0Wm",
        description="БСПБ — хоз. операции от 5к.",
        cda_conditions="Хоз. операции от 5 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Подтвердить при звонке", "Не с физлиц"],
        reject_reasons=["Пополнение от физлиц", "ЗСК", "115-ФЗ"],
    ),
    "uralsib": _offer(
        id="uralsib",
        name="Уралсиб",
        # По прайсу: 3 000 ₽ всего (аванс 500 + основная 2 500)
        payout=2500,
        safe_period_days=45,
        referral_link="https://example.com/uralsib",
        description="Уралсиб — 15к операций или комиссия 1990 ₽.",
        cda_conditions="Операции 15 000 ₽ или комиссия 1 990 ₽.",
        steps=[
            "Данные для заявки и инструкция",
            "Целевое действие (ЦД)",
        ],
        critical_conditions=["Разные ИНН — разные заявки", "Без тех. переводов"],
        reject_reasons=["Фиктивные операции"],
    ),
    "otp": _offer(
        id="otp",
        name="ОТП Банк",
        # По прайсу: 2 000 ₽ всего (аванс 500 + основная 1 500)
        payout=1500,
        safe_period_days=30,
        referral_link="https://rko-group.ru/s/tD5hlGHO",
        description="ОТП — 3 операции от 10к.",
        cda_conditions="3 операции от 10 000 ₽.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Не переводить физлицам"],
        reject_reasons=["115-ФЗ", "Подозрительные операции"],
    ),
    "ubrir": _offer(
        id="ubrir",
        name="УБРиР",
        # По прайсу: 2 000 ₽ всего (аванс 500 + основная 1 500)
        payout=1500,
        safe_period_days=30,
        referral_link="https://trk.ppdu.ru/click/CeoEvohP?erid=Kra23k9bA",
        description="УБРиР — открытие РКО по ссылке.",
        cda_conditions="Открытие счёта и выполнение условий банка.",
        steps=["Ссылка и инструкция", "Целевое действие (ЦД)"],
        critical_conditions=["Только реальные данные", "Один ИНН = одна заявка"],
        reject_reasons=["Дубль", "115-ФЗ", "Закрытие счёта"],
    ),
}

# MFO offers (простые: ссылка + ЦД)
try:
    from mfo_offers import MFO_OFFERS

    for m in MFO_OFFERS:
        OFFERS[m.id] = _offer(
            id=m.id,
            name=f"{m.name} (МФО)",
            payout=m.payout,
            safe_period_days=0,
            referral_link=m.url_template,
            description="МФО оффер: возьми займ *от 4 000 до 15 000 ₽* на *14–21 день*. "
            "Если не даёт больше — оставляем как есть.",
            cda_conditions="Оформить займ по ссылке и выполнить ЦД по условиям ПП.",
            steps=["Ссылка и оформление займа", "ЦД и выплата"],
            critical_conditions=["Только реальные данные", "Не делать дубли"],
            reject_reasons=["Дубль", "Неверные данные", "Отказ МФО"],
            advance_payout=0,
            category="mfo",
        )
except Exception:
    pass


def get_offer(offer_id: str) -> RkoOffer | None:
    return OFFERS.get(offer_id)


def list_offers() -> list[RkoOffer]:
    return list(OFFERS.values())
