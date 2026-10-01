"""GET /api/v1/health for load balancers and container health checks."""
import sqlalchemy as sa
from flask import Blueprint, jsonify

from app.extensions import db

bp = Blueprint("health", __name__)


@bp.get("/api/v1/health")
def health():
    """200 when the app can reach PostgreSQL, 503 otherwise. No sign-in, no data."""
    try:
        db.session.execute(sa.text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any failure means "not ready"
        db.session.rollback()
        return jsonify(status="unavailable", database="unreachable"), 503
    finally:
        db.session.remove()
    return jsonify(status="ok", database="ok")
