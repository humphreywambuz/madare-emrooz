import re

from app.shared.domain.errors import ValidationError

# How mobiles are stored: +98 followed by a 10-digit number starting with 9.
# Also enforced by CHECK constraints on users.mobile and otp_codes.mobile.
IRANIAN_MOBILE_PATTERN = r"^\+989[0-9]{9}$"

# Persian (U+06F0..) and Arabic-Indic (U+0660..) digits, as typed on Iranian keyboards.
_TO_ASCII_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_SEPARATORS = re.compile(r"[\s\-().]")


def to_ascii_digits(value: str) -> str:
    return value.translate(_TO_ASCII_DIGITS)


def normalize_iranian_mobile(raw: str) -> str:
    """Return an Iranian mobile number in E.164 form (``+989121234567``).

    Accepts the ways people type it: ``09121234567``, ``9121234567``,
    ``+98 912 123 4567``, ``0098...``, ``98...`` and Persian digits.
    """
    number = _SEPARATORS.sub("", to_ascii_digits(raw or ""))
    for prefix in ("+98", "0098"):
        if number.startswith(prefix):
            number = number[len(prefix):]
            break
    else:
        if number.startswith("98") and len(number) == 12:
            number = number[2:]
        elif number.startswith("0"):
            number = number[1:]
    if not re.fullmatch(r"9\d{9}", number):
        raise ValidationError("Enter a valid Iranian mobile number, for example 09121234567.")
    return "+98" + number
