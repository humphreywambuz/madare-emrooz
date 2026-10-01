"""Values that migrations spell out by hand must match the code."""
import importlib.util
from pathlib import Path

from app.modules.audit.domain.enums import AuditEventType

VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, next(VERSIONS.glob(f"{name}_*.py")))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_latest_audit_event_check_lists_every_event_type():
    migration = load("f52a06369cf8")
    assert set(migration.NEW_AUDIT_EVENTS) == {e.value for e in AuditEventType}
