from app.modules.audit.domain.enums import AuditEventType
from app.modules.audit.infrastructure.models import AuditLogModel


def test_audit_log_without_actor(session):
    log = AuditLogModel(
        actor_id=None,
        event_type=AuditEventType.ACCESS_DENIED,
        ip_address="192.0.2.10",
        details={"path": "/patients/123"},
    )
    session.add(log)
    session.flush()
    assert log.id is not None
