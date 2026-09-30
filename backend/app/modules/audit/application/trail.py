"""The audit trail other modules write to (spec section 8)."""
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.modules.audit.domain.enums import AuditEventType


@dataclass(frozen=True)
class AuditEvent:
    event_type: AuditEventType
    actor_id: uuid.UUID | None = None
    patient_id: uuid.UUID | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class AuditTrail(Protocol):
    def record(self, event: AuditEvent) -> None:
        """Stage an event in the current transaction; the caller's unit of work commits it."""
