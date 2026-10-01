"""Small helpers shared by every module's routes."""
from flask import request

from app.shared.application.context import Actor, RequestContext

from .auth import current_user


def parse_body(schema):
    return schema.model_validate(request.get_json(silent=True) or {})


def request_context() -> RequestContext:
    user_agent = request.user_agent.string or None
    return RequestContext(
        ip_address=request.remote_addr,
        user_agent=user_agent[:500] if user_agent else None,
    )


def current_actor() -> Actor:
    claims = current_user()
    return Actor(user_id=claims.user_id, role=claims.role, context=request_context())
