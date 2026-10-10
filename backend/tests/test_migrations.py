"""Values that migrations spell out by hand must match the code."""
import importlib.util
from pathlib import Path

from app.modules.audit.domain.enums import AuditEventType

VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"
LATEST_AUDIT_EVENTS_MIGRATION = "398e9e399d54"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, next(VERSIONS.glob(f"{name}_*.py")))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_latest_audit_event_check_lists_every_event_type():
    """Adding an AuditEventType needs a migration that widens the CHECK; update LATEST then."""
    migration = load(LATEST_AUDIT_EVENTS_MIGRATION)
    assert set(migration.NEW_AUDIT_EVENTS) == {e.value for e in AuditEventType}


def test_each_audit_migration_starts_from_the_previous_list():
    previous = load("32eb077dac4a")
    latest = load(LATEST_AUDIT_EVENTS_MIGRATION)
    assert latest.OLD_AUDIT_EVENTS == previous.NEW_AUDIT_EVENTS
