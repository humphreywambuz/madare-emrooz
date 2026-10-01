from datetime import date

from .enums import BloodType


def age_on(birth_date: date, today: date) -> int:
    before_birthday = (today.month, today.day) < (birth_date.month, birth_date.day)
    return today.year - birth_date.year - before_birthday


def rh_incompatibility_risk(mother: BloodType | None, father: BloodType | None) -> bool:
    """Rh-negative mother with an Rh-positive father (candidate for RhoGAM)."""
    return bool(mother and father and mother.is_rh_negative and not father.is_rh_negative)


def is_valid_national_code(code: str) -> bool:
    """Iranian national code (کد ملی): 10 digits whose last digit is a check digit."""
    if len(code) != 10 or not code.isascii() or not code.isdigit() or len(set(code)) == 1:
        return False
    remainder = sum(int(code[i]) * (10 - i) for i in range(9)) % 11
    check = int(code[9])
    return check == remainder if remainder < 2 else check == 11 - remainder
