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
