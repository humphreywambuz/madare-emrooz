from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.modules.pregnancy.domain.enums import CareProviderType, ConceptionType, PregnancyStatus


class StartPregnancyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lmp_date: date
    conception_type: ConceptionType
    avg_cycle_length_days: int = Field(default=28, ge=20, le=45)
    care_provider_type: CareProviderType | None = None
    care_provider_name: str | None = Field(default=None, max_length=200)


class EndPregnancyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: PregnancyStatus


class CorrectPregnancyRequest(BaseModel):
    """Only the fields being corrected."""

    model_config = ConfigDict(extra="forbid")

    lmp_date: date | None = None
    conception_type: ConceptionType | None = None
    avg_cycle_length_days: int | None = Field(default=None, ge=20, le=45)
    care_provider_type: CareProviderType | None = None
    care_provider_name: str | None = Field(default=None, max_length=200)


class CorrectDueDateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimated_due_date: date
    reason: str | None = Field(default=None, max_length=500)  # e.g. "ultrasound at 12 weeks"
