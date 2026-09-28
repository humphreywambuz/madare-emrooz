from enum import StrEnum


class ConceptionType(StrEnum):
    NATURAL = "natural"
    ASSISTED = "assisted"


class CareProviderType(StrEnum):
    SPECIALIST = "specialist"
    MIDWIFE = "midwife"
    HEALTH_CENTER = "health_center"


class PregnancyStatus(StrEnum):
    ACTIVE = "active"
    DELIVERED = "delivered"
    ENDED = "ended"
