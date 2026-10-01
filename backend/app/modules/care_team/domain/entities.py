"""Care team aggregates. Pure Python: no Flask, no SQLAlchemy."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from app.shared.domain.errors import ValidationError

from .enums import AlertKind, ApprovalScope, CareRole


@dataclass
class StaffProfile:
    """What mothers see when they choose a midwife; the account itself lives in identity."""

    user_id: uuid.UUID
    first_name: str
    last_name: str
    bio: str | None = None
    is_listed: bool = True


@dataclass
class CareAssignment:
    """A mother chose this staff member. Ending it keeps the history."""

    patient_id: uuid.UUID
    staff_id: uuid.UUID
    care_role: CareRole
    started_at: datetime
    ended_at: datetime | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    def end(self, now: datetime) -> None:
        if self.ended_at is None:
            self.ended_at = now


@dataclass
class Alert:
    """A red alert for the care team, e.g. the mother reported bleeding."""

    patient_id: uuid.UUID
    kind: AlertKind
    created_at: datetime
    daily_log_id: uuid.UUID | None = None
    seen_at: datetime | None = None
    seen_by_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def mark_seen(self, by: uuid.UUID, now: datetime) -> None:
        if self.seen_at is not None:
            raise ValidationError("This alert has already been marked as seen.")
        self.seen_at = now
        self.seen_by_id = by


@dataclass
class CareApproval:
    """A doctor's approval checkmark, e.g. for the rehabilitation plan. Revoking keeps the row."""

    patient_id: uuid.UUID
    approved_by_id: uuid.UUID
    scope: ApprovalScope
    approved_at: datetime
    revoked_at: datetime | None = None
    revoked_by_id: uuid.UUID | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def revoke(self, by: uuid.UUID, now: datetime) -> None:
        self.revoked_at = now
        self.revoked_by_id = by
