import uuid
from typing import Protocol

from .context import Actor


class PatientAccess(Protocol):
    """Checks that a staff member may open a mother's record (implemented by the care team)."""

    def require_record_access(self, actor: Actor, patient_id: uuid.UUID) -> None:
        """Raises NotFoundError for an unknown mother and PermissionDeniedError (audited)
        if she is not the actor's patient."""

    def record_viewed(
        self, actor: Actor, patient_id: uuid.UUID, resource: str, resource_id: object = None
    ) -> None:
        """Write the view to the audit log and commit."""
