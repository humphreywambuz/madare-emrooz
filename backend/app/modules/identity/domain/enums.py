from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    DOCTOR = "doctor"
    MIDWIFE = "midwife"
    ADMIN = "admin"


STAFF_ROLES = frozenset({UserRole.DOCTOR, UserRole.MIDWIFE, UserRole.ADMIN})
