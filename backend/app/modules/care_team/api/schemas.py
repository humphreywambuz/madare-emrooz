import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.modules.care_team.domain.enums import ApprovalScope, RiskTag
from app.modules.identity.domain.enums import UserRole


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateStaffBody(_Body):
    mobile: str = Field(min_length=1, max_length=32)
    role: UserRole
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    is_listed: bool = True


class UpdateStaffBody(_Body):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=2000)
    is_listed: bool | None = None
    is_active: bool | None = None


class ChooseMidwifeBody(_Body):
    midwife_id: uuid.UUID


class NoteBody(_Body):
    body: str = Field(min_length=1, max_length=5000)


class RiskTagBody(_Body):
    tag: RiskTag
    note: str | None = Field(default=None, max_length=255)


class ApprovalBody(_Body):
    scope: ApprovalScope


class PatientListQuery(_Body):
    q: str | None = Field(default=None, max_length=100)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
