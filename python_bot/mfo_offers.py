"""Офферы МФО."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MfoOffer:
    id: str
    name: str
    payout: int
    rate_text: str
    url_template: str


MFO_OFFERS: list[MfoOffer] = [
    MfoOffer(
        id="mfo_zaymer",
        name="Займер",
        payout=4425,
        rate_text="4425 ₽",
        url_template="https://t.fincpanetwork.ru/click/24568/15/?erid=2W5zFHwA2h6?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_moneyman",
        name="MoneyMan",
        payout=3700,
        rate_text="3700 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=1253&erid=2SDnjdTrs6M?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_bystrodengi",
        name="Быстроденьги",
        payout=4194,
        rate_text="4194 ₽",
        url_template="https://t.fincpanetwork.ru/click/24568/613/?erid=LjN8JtHPe?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_migkredit",
        name="МигКредит",
        payout=4185,
        rate_text="4185 ₽",
        url_template="https://t.fincpanetwork.ru/click/24568/450/?erid=2W5zFHt2Zms?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_adengi",
        name="А-Деньги",
        payout=3000,
        rate_text="3000 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=1924&erid=2SDnjeV7aM9?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_maxcredit",
        name="MaxCredit",
        payout=4400,
        rate_text="4400 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=1062&erid=2SDnjbuHuCz?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_umnye",
        name="Умные наличные",
        payout=4400,
        rate_text="4400 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=2259&erid=2SDnjebTPH3&sub1={sub1}&siteId=18278",
    ),
    MfoOffer(
        id="mfo_svoi",
        name="Свои Люди",
        payout=2700,
        rate_text="2700 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=1728&erid=2SDnjd2dyNy?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_srochno",
        name="Срочно Деньги",
        payout=2400,
        rate_text="2400 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=1701&erid=2SDnjeVT5Gb?sub1={sub1}",
    ),
    MfoOffer(
        id="mfo_rocketman",
        name="RocketMan",
        payout=2600,
        rate_text="2600 ₽",
        url_template="https://trk.ppdu.ru/click?uid=321413&oid=1843&erid=2SDnjdR3AZv?sub1={sub1}",
    ),
]

