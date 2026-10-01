import re

import pytest

from app.modules.identity.domain.mobile import IRANIAN_MOBILE_PATTERN, normalize_iranian_mobile
from app.shared.domain.errors import ValidationError


@pytest.mark.parametrize(
    "raw",
    [
        "09121234567",
        "9121234567",
        "+989121234567",
        "00989121234567",
        "989121234567",
        "+98 912 123 4567",
        "0912-123-4567",
        "۰۹۱۲۱۲۳۴۵۶۷",  # Persian digits
        "٠٩١٢١٢٣٤٥٦٧",  # Arabic-Indic digits
    ],
)
def test_accepts_common_formats(raw):
    normalized = normalize_iranian_mobile(raw)
    assert normalized == "+989121234567"
    # What the app saves must satisfy the database CHECK constraint.
    assert re.fullmatch(IRANIAN_MOBILE_PATTERN, normalized)


@pytest.mark.parametrize("raw", ["", "12345", "02112345678", "+441234567890", "0912123456", "091212345678"])
def test_rejects_non_mobile_numbers(raw):
    with pytest.raises(ValidationError):
        normalize_iranian_mobile(raw)
