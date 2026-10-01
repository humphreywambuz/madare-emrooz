"""How the staff panel's patient search box is read."""
from dataclasses import dataclass

from app.modules.identity.domain.mobile import to_ascii_digits

# Arabic letters people often type instead of the Persian ones (ي → ی, ك → ک).
ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ك": "ک", "ى": "ی"})


@dataclass(frozen=True)
class PatientSearch:
    """Either digits (part of a mobile number or national code) or name words."""

    digits: str | None = None
    words: tuple[str, ...] = ()


def parse_patient_search(text: str | None) -> PatientSearch | None:
    """``"0912 123"`` → digits ``9121 23``-style match on the mobile; ``"سارا احمدی"`` → two
    words, each of which must appear in the first or last name. Persian digits are accepted."""
    text = to_ascii_digits(text or "").translate(ARABIC_TO_PERSIAN).strip()
    if not text:
        return None
    compact = "".join(ch for ch in text if ch not in " +-()")
    if compact.isdigit():
        # Local form 0912… is stored as +98912…: drop the leading 0 (or 0098) to match.
        if compact.startswith("0098"):
            compact = compact[4:]
        elif compact.startswith("0"):
            compact = compact[1:]
        return PatientSearch(digits=compact or None) if compact else None
    return PatientSearch(words=tuple(text.lower().split()))
