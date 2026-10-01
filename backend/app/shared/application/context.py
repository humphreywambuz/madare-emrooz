"""Who is making a request and from where. Passed into use cases for access checks and the audit log."""
import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class Actor:
    """The signed-in user performing a use case."""

    user_id: uuid.UUID
    role: str
    context: RequestContext = field(default_factory=RequestContext)
