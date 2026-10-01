"""Partner Mode use cases. Depend only on ports, never on Flask or SQLAlchemy."""
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.pregnancy.domain.partner import PartnerLink, parse_partner_token, partner_token
from app.shared.application.context import Actor, RequestContext
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import NotFoundError, ValidationError

from .ports import PartnerLinkRepository, PregnancyRepository


@dataclass(frozen=True)
class PartnerLinkView:
    token: str
    created_at: datetime


@dataclass(frozen=True)
class PartnerPregnancyView:
    """Everything the spouse sees: no name, no medical data, no alerts."""

    gestational_week: int
    gestational_days: int  # days into the current week
    estimated_due_date: date
    days_until_due: int


class PartnerService:
    def __init__(
        self,
        *,
        links: PartnerLinkRepository,
        pregnancies: PregnancyRepository,
        audit: AuditTrail,
        uow: UnitOfWork,
        secret_key: str,
        today: Callable[[], date] = date.today,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._links = links
        self._pregnancies = pregnancies
        self._audit = audit
        self._uow = uow
        self._secret_key = secret_key
        self._today = today
        self._now = now

    def create_link(self, actor: Actor) -> PartnerLinkView:
        """A new QR code. Any previous one stops working."""
        if self._pregnancies.get_active_for_user(actor.user_id) is None:
            raise ValidationError("The partner code is available during an active pregnancy.")
        now = self._now()
        current = self._links.active_for_user(actor.user_id)
        if current is not None:
            current.revoke(now)
            self._links.save(current)
        link = PartnerLink(actor.user_id, created_at=now)
        self._links.add(link)
        self._record(AuditEventType.PARTNER_LINK_CREATED, actor.user_id, actor, link)
        self._uow.commit()
        return self._view(link)

    def current_link(self, user_id: uuid.UUID) -> PartnerLinkView:
        link = self._links.active_for_user(user_id)
        if link is None:
            raise NotFoundError("The partner code is turned off.")
        return self._view(link)

    def revoke_link(self, actor: Actor) -> None:
        link = self._links.active_for_user(actor.user_id)
        if link is None:
            return
        link.revoke(self._now())
        self._links.save(link)
        self._record(AuditEventType.PARTNER_LINK_REVOKED, actor.user_id, actor, link)
        self._uow.commit()

    def view(self, token: str, context: RequestContext) -> PartnerPregnancyView:
        """What the spouse sees after scanning. Every view is written to the audit log."""
        link_id = parse_partner_token(self._secret_key, token)
        link = self._links.get(link_id) if link_id else None
        pregnancy = self._pregnancies.get_active_for_user(link.user_id) if link and link.is_active else None
        if pregnancy is None:
            # The same answer for a forged, revoked or finished link: nothing to learn from it.
            raise NotFoundError("This code is not active.")
        today = self._today()
        age_days = pregnancy.gestational_age_days(today)
        self._record(AuditEventType.PARTNER_LINK_VIEWED, link.user_id, None, link, context)
        self._uow.commit()
        return PartnerPregnancyView(
            gestational_week=age_days // 7,
            gestational_days=age_days % 7,
            estimated_due_date=pregnancy.estimated_due_date,
            days_until_due=max((pregnancy.estimated_due_date - today).days, 0),
        )

    def _view(self, link: PartnerLink) -> PartnerLinkView:
        return PartnerLinkView(partner_token(self._secret_key, link.id), link.created_at)

    def _record(self, event_type, patient_id, actor: Actor | None, link: PartnerLink, context=None):
        context = context or (actor.context if actor else RequestContext())
        self._audit.record(
            AuditEvent(
                event_type,
                actor_id=actor.user_id if actor else None,
                patient_id=patient_id,
                resource_type="partner_link",
                resource_id=str(link.id),
                ip_address=context.ip_address,
                user_agent=context.user_agent,
            )
        )
