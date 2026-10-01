"""Errors raised by domain and application code.

They carry no HTTP knowledge; ``app.shared.api.errors`` maps them to responses.
"""


class DomainError(Exception):
    """Base class for expected, user-facing errors."""

    code = "domain_error"

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(DomainError):
    code = "validation_error"


class NotFoundError(DomainError):
    code = "not_found"


class ConflictError(DomainError):
    code = "conflict"


class AuthenticationError(DomainError):
    code = "unauthenticated"


class PermissionDeniedError(DomainError):
    code = "permission_denied"


class ServiceUnavailableError(DomainError):
    """A service we depend on (e.g. the SMS gateway) failed; the client can retry."""

    code = "service_unavailable"


class RateLimitedError(DomainError):
    """Too many attempts; ``retry_after_seconds`` tells the client when to try again."""

    code = "rate_limited"

    def __init__(self, message: str, *, retry_after_seconds: int):
        super().__init__(message, details={"retry_after_seconds": retry_after_seconds})
        self.retry_after_seconds = retry_after_seconds
