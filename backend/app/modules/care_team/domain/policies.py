"""Who in the care team may see which mother."""
import uuid

from app.modules.identity.domain.enums import UserRole

from .enums import DoctorPatientScope


def can_open_record(
    *,
    viewer_id: uuid.UUID,
    viewer_role: str,
    midwife_id: uuid.UUID | None,
    doctor_id: uuid.UUID | None,
    doctor_scope: DoctorPatientScope,
) -> bool:
    """A midwife sees only the mothers who chose her. A doctor sees every mother in
    Phase 1, and only the mothers who chose them once DOCTOR_PATIENT_SCOPE is
    "assigned" (Phase 2). Admins manage accounts and unassigned alerts, not records."""
    if viewer_role == UserRole.MIDWIFE:
        return midwife_id == viewer_id
    if viewer_role == UserRole.DOCTOR:
        return doctor_scope is DoctorPatientScope.ALL or doctor_id == viewer_id
    return False


def alert_goes_to_admins(midwife_id: uuid.UUID | None) -> bool:
    """An alert from a mother who hasn't chosen a midwife yet must still be seen:
    it appears in the admins' "unassigned mothers" list."""
    return midwife_id is None
