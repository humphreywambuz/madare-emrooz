from flask import Flask, jsonify
from pydantic import ValidationError as PydanticValidationError

from app.shared.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

_STATUS = {
    ValidationError: 422,
    NotFoundError: 404,
    ConflictError: 409,
    AuthenticationError: 401,
    PermissionDeniedError: 403,
}


def _status_for(error: DomainError) -> int:
    for cls in type(error).__mro__:
        if cls in _STATUS:
            return _STATUS[cls]
    return 400


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(error: DomainError):
        body = {"error": {"code": error.code, "message": error.message, "details": error.details}}
        return jsonify(body), _status_for(error)

    @app.errorhandler(PydanticValidationError)
    def handle_request_validation(error: PydanticValidationError):
        details = [
            {"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]}
            for e in error.errors(include_url=False)
        ]
        body = {
            "error": {
                "code": "validation_error",
                "message": "The request body is invalid.",
                "details": {"fields": details},
            }
        }
        return jsonify(body), 422
