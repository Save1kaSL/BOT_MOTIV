import re


def parse_application(text: str) -> dict[str, str] | None:
    fields: dict[str, str] = {}
    patterns: list[tuple[re.Pattern[str], str]] = [
        (re.compile(r"инн[:\s]+(.+)", re.I), "inn"),
        (re.compile(r"фио[:\s]+(.+)", re.I), "full_name"),
        (re.compile(r"телефон[:\s]+(.+)", re.I), "phone"),
        (re.compile(r"почта[:\s]+(.+)", re.I), "email"),
        (re.compile(r"email[:\s]+(.+)", re.I), "email"),
        (re.compile(r"город[:\s]+(.+)", re.I), "city"),
    ]
    for line in text.split("\n"):
        for regex, key in patterns:
            m = regex.match(line.strip())
            if m:
                fields[key] = m.group(1).strip()
    return fields if len(fields) >= 3 else None


def normalize_inn(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def is_valid_inn(value: str) -> bool:
    inn = normalize_inn(value)
    return len(inn) in (10, 12)


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def is_valid_phone(value: str) -> bool:
    phone = normalize_phone(value)
    return len(phone) == 11 and phone.startswith("7")


def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (value or "").strip()))


def is_valid_full_name(value: str) -> bool:
    parts = [p for p in (value or "").strip().split() if p]
    return len(parts) >= 2
