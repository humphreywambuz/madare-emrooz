from enum import StrEnum


class RiskTag(StrEnum):
    NEEDS_RHOGAM = "needs_rhogam"
    THYROID = "thyroid"
    MISCARRIAGE_HISTORY = "miscarriage_history"
    DIABETES = "diabetes"
    HYPERTENSION = "hypertension"
    ANEMIA = "anemia"
    INFECTIOUS_DISEASE = "infectious_disease"
    OTHER = "other"


class ApprovalScope(StrEnum):
    PREGNANCY_PLAN = "pregnancy_plan"
    REHABILITATION_PLAN = "rehabilitation_plan"
