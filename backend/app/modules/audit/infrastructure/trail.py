from sqlalchemy.orm import Session

from app.modules.audit.application.trail import AuditEvent

from .models import AuditLogModel


class SqlAlchemyAuditTrail:
    """Implements ``application.trail.AuditTrail``: adds a row to the caller's transaction."""

    def __init__(self, session: Session):
        self._session = session

    def record(self, event: AuditEvent) -> None:
        self._session.add(
            AuditLogModel(
                actor_id=event.actor_id,
                patient_id=event.patient_id,
                event_type=event.event_type,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                ip_address=event.ip_address,
                user_agent=event.user_agent,
                details=event.details or None,
            )
        )
