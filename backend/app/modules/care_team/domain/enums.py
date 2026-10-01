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


class CareRole(StrEnum):
    """The role a staff member plays for one mother. Phase 1 assigns midwives only;
    Phase 2 adds the mother's own gynecologist / referring doctor."""

    MIDWIFE = "midwife"
    DOCTOR = "doctor"


class DoctorPatientScope(StrEnum):
    """Which mothers a doctor can open (setting DOCTOR_PATIENT_SCOPE)."""

    ALL = "all"  # Phase 1: no doctor is assigned yet, so doctors see every mother
    ASSIGNED = "assigned"  # Phase 2: only mothers who chose this doctor


class AlertKind(StrEnum):
    BLEEDING = "bleeding"
