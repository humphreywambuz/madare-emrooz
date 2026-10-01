"""Read models returned by the care team use cases."""
import uuid
from dataclasses import dataclass
from datetime import datetime

from app.modules.care_team.domain.enums import AlertKind


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
