"""Feature modules. Each one follows the same layering:

    domain/          entities, enums and business rules (pure Python)
    application/     use cases and the ports (interfaces) they need
    infrastructure/  SQLAlchemy models and repositories implementing the ports
    api/             Flask blueprint: HTTP in, use case call, JSON out

See backend/docs/architecture.md.
"""
from importlib import import_module

from flask import Flask

MODULES = (
    "identity",        # §1  users, OTP, sessions
    "profiles",        # §2-3 demographic profile, medical history
    "pregnancy",       # §4  pregnancy path
    "monitoring",      # §5  daily logs
    "documents",       # §6  medical documents
    "care_team",       # §7  risk tags, staff notes, approvals
    "audit",           # §8  audit log
    "fitness",         # §9  fitness path
    "rehabilitation",  # §10-11 rehab profile and access control
)


def register_models() -> None:
    """Import every module's ORM models so SQLAlchemy/Alembic see all tables."""
    for name in MODULES:
        import_module(f"app.modules.{name}.infrastructure.models")


def register_blueprints(app: Flask) -> None:
    for name in MODULES:
        try:
            routes = import_module(f"app.modules.{name}.api.routes")
        except ModuleNotFoundError as exc:
            if exc.name not in (f"app.modules.{name}.api", f"app.modules.{name}.api.routes"):
                raise
            continue  # module has no HTTP API yet
        app.register_blueprint(routes.bp)
