"""Read models returned by the care team use cases."""
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.care_team.domain.enums import AlertKind, ApprovalScope, RiskTag


@dataclass(frozen=True)
class StaffView:
    user_id: uuid.UUID
    role: str
    mobile: str
    first_name: str | None
    last_name: str | None
    bio: str | None
    is_listed: bool
    is_active: bool


@dataclass(frozen=True)
class MidwifeOption:
    """A midwife as mothers see her in the app: no mobile number."""

    id: uuid.UUID
    first_name: str
    last_name: str
    bio: str | None


@dataclass(frozen=True)
class AlertView:
    id: uuid.UUID
    kind: AlertKind
    created_at: datetime
    seen_at: datetime | None
    patient_id: uuid.UUID
    patient_first_name: str | None
    patient_last_name: str | None
    patient_mobile: str


@dataclass(frozen=True)
class PatientRow:
    id: uuid.UUID
    mobile: str
    first_name: str | None
    last_name: str | None
    join_goal: str | None
    reproductive_status: str | None
    midwife_id: uuid.UUID | None
    open_alerts: int
    last_alert_at: datetime | None


@dataclass(frozen=True)
class NoteView:
    id: uuid.UUID
    body: str
    created_at: datetime
    author_id: uuid.UUID
    author_name: str | None
    author_role: str


@dataclass(frozen=True)
class RiskTagView:
    tag: RiskTag
    source: str  # "record": follows from her profile/history; "staff": added by a clinician
    note: str | None = None
    added_by_id: uuid.UUID | None = None


@dataclass(frozen=True)
class ApprovalView:
    id: uuid.UUID
    scope: ApprovalScope
    approved_by_id: uuid.UUID
    approved_at: datetime
    revoked_at: datetime | None
    revoked_by_id: uuid.UUID | None
    is_active: bool


@dataclass(frozen=True)
class PatientPage:
    items: list[PatientRow]
    page: int
    per_page: int
    total: int
