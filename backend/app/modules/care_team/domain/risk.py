"""Summary-card risk tags that follow from the mother's own record."""
from dataclasses import dataclass

from .enums import RiskTag


@dataclass(frozen=True)
class PatientFacts:
    rh_incompatibility_risk: bool = False
    miscarriage_count: int | None = None
    has_diabetes: bool | None = None
    has_hypertension: bool | None = None
    has_thyroid_disorder: bool | None = None
    has_infectious_disease: bool | None = None  # HIV, hepatitis B or C


def derive_risk_tags(facts: PatientFacts) -> set[RiskTag]:
    """Red flags a clinician should see within seconds, without anyone adding them by hand."""
    rules = {
        RiskTag.NEEDS_RHOGAM: facts.rh_incompatibility_risk,
        RiskTag.MISCARRIAGE_HISTORY: bool(facts.miscarriage_count),
        RiskTag.DIABETES: facts.has_diabetes is True,
        RiskTag.HYPERTENSION: facts.has_hypertension is True,
        RiskTag.THYROID: facts.has_thyroid_disorder is True,
        RiskTag.INFECTIOUS_DISEASE: facts.has_infectious_disease is True,
    }
    return {tag for tag, applies in rules.items() if applies}
