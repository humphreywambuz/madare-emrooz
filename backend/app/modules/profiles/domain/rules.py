from datetime import date

from .enums import BloodType


def age_on(birth_date: date, today: date) -> int:
    before_birthday = (today.month, today.day) < (birth_date.month, birth_date.day)
    return today.year - birth_date.year - before_birthday


def rh_incompatibility_risk(mother: BloodType | None, father: BloodType | None) -> bool:
    """Rh-negative mother with an Rh-positive father (candidate for RhoGAM)."""
    return bool(mother and father and mother.is_rh_negative and not father.is_rh_negative)
