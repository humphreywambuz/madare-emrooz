"""HTTP adapter for the pregnancy module: parse the request, call a use case,
serialise the result. No business rules live here."""
from dataclasses import asdict

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.modules.pregnancy.application.services import PregnancyService, StartPregnancy
from app.modules.pregnancy.infrastructure.repository import SqlAlchemyPregnancyRepository
from app.shared.api.auth import current_user, login_required
from app.shared.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

from .schemas import EndPregnancyRequest, StartPregnancyRequest

bp = Blueprint("pregnancy", __name__, url_prefix="/api/v1/pregnancies")


def _service() -> PregnancyService:
    return PregnancyService(
        SqlAlchemyPregnancyRepository(db.session), SqlAlchemyUnitOfWork(db.session)
    )


@bp.post("")
@login_required
def start_pregnancy():
    body = StartPregnancyRequest.model_validate(request.get_json(silent=True) or {})
    view = _service().start(StartPregnancy(user_id=current_user().user_id, **body.model_dump()))
    return jsonify(asdict(view)), 201


@bp.get("/current")
@login_required
def get_current_pregnancy():
    return jsonify(asdict(_service().get_active(current_user().user_id)))


@bp.post("/current/end")
@login_required
def end_current_pregnancy():
    body = EndPregnancyRequest.model_validate(request.get_json(silent=True) or {})
    return jsonify(asdict(_service().end_active(current_user().user_id, body.status)))
