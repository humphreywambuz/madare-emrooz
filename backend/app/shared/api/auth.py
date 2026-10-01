import uuid
from collections.abc import Callable
from functools import wraps

from flask import Flask, current_app, g, request

from app.shared.domain.errors import AuthenticationError, PermissionDeniedError
from app.shared.infrastructure.tokens import AccessTokenService, TokenClaims


_USER_IS_ACTIVE = "auth.user_is_active"


def register_user_status_check(app: Flask, is_active: Callable[[uuid.UUID], bool]) -> None:
    """Tell ``login_required`` how to check that a token's user may still sign in.

    Provided by the identity module and wired in ``create_app``, so shared code
    never imports a feature module.
    """
    app.extensions[_USER_IS_ACTIVE] = is_active


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
        claims = token_service().verify(token)
        is_active = current_app.extensions.get(_USER_IS_ACTIVE)
        if is_active is None:
            raise RuntimeError("No user status check registered; see register_user_status_check.")
        # Tokens stay valid until they expire, so a deactivated or deleted
        # account must be rejected here on every request.
        if not is_active(claims.user_id):
            raise AuthenticationError("This account is no longer active.")
        g.current_user = claims
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
