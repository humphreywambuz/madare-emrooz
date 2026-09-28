"""Enumerations used by the Phase 1 (MVP) data model.

Values are persisted as strings, so renaming a value requires a data migration.
"""
from enum import StrEnum


# 1. Auth & roles
class UserRole(StrEnum):
    USER = "user"
    DOCTOR = "doctor"
    MIDWIFE = "midwife"
    ADMIN = "admin"


# 2. Demographic profile
class BloodType(StrEnum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"

    @property
    def is_rh_negative(self) -> bool:
        return self.value.endswith("-")


class ReproductiveStatus(StrEnum):
    TRYING_TO_CONCEIVE = "trying_to_conceive"
    PREGNANT = "pregnant"
    POSTPARTUM = "postpartum"


class JoinGoal(StrEnum):
    PREGNANCY = "pregnancy"
    FITNESS = "fitness"
    REHABILITATION = "rehabilitation"


# 4. Pregnancy path
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


# 6. Medical documents
class DocumentType(StrEnum):
    BLOOD_TEST = "blood_test"
    URINE_TEST = "urine_test"
    THYROID_TEST = "thyroid_test"
    ULTRASOUND = "ultrasound"
    SCREENING = "screening"
    IMAGING = "imaging"  # radiology / MRI (orthopedic referral)
    OTHER = "other"


# 7. Medical staff panel
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


# 8. Audit log
class AuditEventType(StrEnum):
    PROFILE_CREATED = "profile_created"
    RECORD_VIEWED = "record_viewed"
    RECORD_UPDATED = "record_updated"
    ACCESS_DENIED = "access_denied"
    LOGIN_SUCCEEDED = "login_succeeded"
    LOGIN_FAILED = "login_failed"
    DOCUMENT_UPLOADED = "document_uploaded"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REVOKED = "approval_revoked"


# 9. Fitness path
class FitnessGoal(StrEnum):
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"
    OTHER = "other"


# 10. Rehabilitation path
class RehabSubcategory(StrEnum):
    INJURY_CORRECTION = "injury_correction"
    POSTPARTUM_RECOVERY = "postpartum_recovery"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    YOGA_MEDITATION = "yoga_meditation"
    ORTHOPEDIC_REFERRAL = "orthopedic_referral"


class InjuryOnset(StrEnum):
    RECENT = "recent"
    ONE_TO_SIX_MONTHS = "one_to_six_months"
    CHRONIC = "chronic"  # more than 6 months


class PainType(StrEnum):
    SHOOTING = "shooting"
    BURNING_TINGLING = "burning_tingling"
    DULL_ACHING = "dull_aching"


class TimeSinceDelivery(StrEnum):
    UNDER_40_DAYS = "under_40_days"
    TWO_TO_SIX_MONTHS = "two_to_six_months"
    OVER_SIX_MONTHS = "over_six_months"


class TrainingGoal(StrEnum):
    STRESS_REDUCTION = "stress_reduction"
    FLEXIBILITY = "flexibility"
    POSTURE_CORRECTION = "posture_correction"
    CHRONIC_STIFFNESS_RELIEF = "chronic_stiffness_relief"


class FitnessLevel(StrEnum):
    INACTIVE = "inactive"
    BEGINNER = "beginner"
    PROFESSIONAL = "professional"


class OrthopedicReferralReason(StrEnum):
    SEVERE_JOINT_PAIN = "severe_joint_pain"
    INJURY_FRACTURE = "injury_fracture"
    SPINE_CHECKUP = "spine_checkup"
