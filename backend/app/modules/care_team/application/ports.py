import uuid
from typing import Protocol

from app.modules.care_team.domain.entities import Alert, CareAssignment, StaffProfile
from app.modules.care_team.domain.enums import CareRole
from app.modules.identity.domain.entities import User
from app.modules.identity.domain.enums import UserRole

from .views import AlertView, MidwifeOption, PatientRow, StaffView


class StaffAccounts(Protocol):
    """User accounts, owned by the identity module. Calls don't commit."""

    def create_staff(self, raw_mobile: str, role: UserRole) -> uuid.UUID: ...

    def get(self, user_id: uuid.UUID) -> User | None: ...

    def set_active(self, user_id: uuid.UUID, active: bool) -> None: ...


class StaffProfileRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> StaffProfile | None: ...

    def save(self, profile: StaffProfile) -> None: ...


class StaffDirectory(Protocol):
    def get_staff(self, user_id: uuid.UUID) -> StaffView | None: ...

    def list_staff(self) -> list[StaffView]: ...

    def list_listed_midwives(self) -> list[MidwifeOption]:
        """Active midwives that admins have listed for mothers to choose from."""


class CareAssignmentRepository(Protocol):
    def active_for_patient(self, patient_id: uuid.UUID, role: CareRole) -> CareAssignment | None: ...

    def active_for_staff(self, staff_id: uuid.UUID, role: CareRole) -> list[CareAssignment]: ...

    def add(self, assignment: CareAssignment) -> None:
        """Raises ConflictError if the mother already has an active assignment for that role."""

    def save(self, assignment: CareAssignment) -> None: ...


class AlertRepository(Protocol):
    def add(self, alert: Alert) -> None: ...

    def get(self, alert_id: uuid.UUID) -> Alert | None: ...

    def save(self, alert: Alert) -> None: ...

    def open_for_midwife(self, midwife_id: uuid.UUID) -> list[AlertView]: ...

    def open_unassigned(self) -> list[AlertView]:
        """Unseen alerts from mothers with no midwife."""


class PatientDirectory(Protocol):
    def is_patient(self, user_id: uuid.UUID) -> bool:
        """True for an app user (role "user"), i.e. a mother."""

    def list_patients(
        self, *, staff_id: uuid.UUID | None = None, role: CareRole | None = None
    ) -> list[PatientRow]:
        """Every mother, or only those assigned to ``staff_id`` in ``role``. Open alerts first."""
