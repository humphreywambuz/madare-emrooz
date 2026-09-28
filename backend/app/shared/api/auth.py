from functools import wraps

from flask import current_app, g, request

from app.shared.domain.errors import AuthenticationError, PermissionDeniedError
from app.shared.infrastructure.tokens import AccessTokenService, TokenClaims


def token_service() -> AccessTokenService:
    return AccessTokenService(
        current_app.config["SECRET_KEY"], current_app.config["ACCESS_TOKEN_TTL_SECONDS"]
    )


def current_user() -> TokenClaims:
    return g.current_user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthenticationError("Sign in to continue.")
        g.current_user = token_service().verify(token)
        return view(*args, **kwargs)

    return wrapper


def roles_required(*roles: str):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapper(*args, **kwargs):
            if current_user().role not in roles:
                raise PermissionDeniedError("You do not have access to this resource.")
            return view(*args, **kwargs)

        return wrapper

    return decorator
