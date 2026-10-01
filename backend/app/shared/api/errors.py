from flask import Flask, jsonify
from pydantic import ValidationError as PydanticValidationError
from werkzeug.exceptions import RequestEntityTooLarge

from app.shared.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ServiceUnavailableError,
    ValidationError,
)

_STATUS = {
    ValidationError: 422,
    NotFoundError: 404,
    ConflictError: 409,
    AuthenticationError: 401,
    PermissionDeniedError: 403,
    RateLimitedError: 429,
    ServiceUnavailableError: 503,
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
        headers = {}
        if isinstance(error, RateLimitedError):
            headers["Retry-After"] = str(error.retry_after_seconds)
        return jsonify(body), _status_for(error), headers

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(error: RequestEntityTooLarge):
        body = {"error": {"code": "too_large", "message": "The upload is too large.", "details": {}}}
        return jsonify(body), 413

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
