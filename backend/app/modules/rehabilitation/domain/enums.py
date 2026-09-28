from enum import StrEnum


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
