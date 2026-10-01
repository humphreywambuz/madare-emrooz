"""Care team use cases: staff accounts, choosing a midwife, record access and red alerts.

Depend only on ports, never on Flask or SQLAlchemy.
"""
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from app.modules.audit.application.trail import AuditEvent, AuditTrail
from app.modules.audit.domain.enums import AuditEventType
from app.modules.care_team.domain.entities import (
    Alert,
    CareApproval,
    CareAssignment,
    RiskTagAssignment,
    StaffNote,
    StaffProfile,
)
from app.modules.care_team.domain.enums import (
    AlertKind,
    ApprovalScope,
    CareRole,
    DoctorPatientScope,
    RiskTag,
)
from app.modules.care_team.domain.policies import alert_goes_to_admins, can_open_record
from app.modules.care_team.domain.risk import PatientFacts, derive_risk_tags
from app.modules.identity.domain.enums import UserRole
from app.shared.application.access import PatientAccess
from app.shared.application.context import Actor
from app.shared.application.unit_of_work import UnitOfWork
from app.shared.domain.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)

from .ports import (
    AlertRepository,
    ApprovalRepository,
    CareAssignmentRepository,
    PatientDirectory,
    RiskTagRepository,
    StaffAccounts,
    StaffDirectory,
    StaffNoteRepository,
    StaffProfileRepository,
)
from .views import (
    AlertView,
    ApprovalView,
    MidwifeOption,
    NoteView,
    PatientRow,
    RiskTagView,
    StaffView,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _audit_event(
    event_type: AuditEventType,
    actor: Actor | None,
    *,
    patient_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: object = None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        event_type,
        actor_id=actor.user_id if actor else None,
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=actor.context.ip_address if actor else None,
        user_agent=actor.context.user_agent if actor else None,
        details=details or {},
    )


class StaffService:
    """Admins create and list staff; mothers choose their midwife from the listed ones."""

    def __init__(
        self,
        *,
        accounts: StaffAccounts,
        profiles: StaffProfileRepository,
        directory: StaffDirectory,
        assignments: CareAssignmentRepository,
        audit: AuditTrail,
        uow: UnitOfWork,
        now: Callable[[], datetime] = _utcnow,
    ):
        self._accounts = accounts
        self._profiles = profiles
        self._directory = directory
        self._assignments = assignments
        self._audit = audit
        self._uow = uow
        self._now = now

    # --- admins ------------------------------------------------------------------

    def create_staff(
        self,
        actor: Actor | None,
        *,
        mobile: str,
        role: UserRole,
        first_name: str,
        last_name: str,
        bio: str | None = None,
        is_listed: bool = True,
    ) -> StaffView:
        """``actor`` is None when an admin is created from the command line."""
        user_id = self._accounts.create_staff(mobile, role)
        self._profiles.save(
            StaffProfile(user_id, first_name.strip(), last_name.strip(), bio, is_listed)
        )
        self._audit.record(
            _audit_event(
                AuditEventType.STAFF_ACCOUNT_CREATED, actor,
                resource_type="user", resource_id=user_id, details={"role": role.value},
            )
        )
        self._uow.commit()
        return self._directory.get_staff(user_id)

    def list_staff(self) -> list[StaffView]:
        return self._directory.list_staff()

    def update_staff(self, actor: Actor, user_id: uuid.UUID, changes: dict[str, Any]) -> StaffView:
        """Change name, bio, whether mothers can choose her (is_listed) or the account (is_active)."""
        account = self._accounts.get(user_id)
        profile = self._profiles.get(user_id)
        if account is None or profile is None:
            raise NotFoundError("Staff member not found.")
        cleared = sorted(k for k, v in changes.items() if v is None and k != "bio")
        if cleared:
            raise ValidationError("These fields can't be empty.", details={"fields": cleared})
        for name in ("first_name", "last_name", "bio", "is_listed"):
            if name in changes:
                setattr(profile, name, changes[name])
        self._profiles.save(profile)
        if "is_active" in changes and changes["is_active"] != account.is_active:
            self._accounts.set_active(user_id, changes["is_active"])
            if not changes["is_active"]:
                # Her mothers must not send alerts to an account nobody reads: they go
                # back to the admins' unassigned list until each mother chooses again.
                for assignment in self._assignments.active_for_staff(user_id, CareRole.MIDWIFE):
                    assignment.end(self._now())
                    self._assignments.save(assignment)
        self._audit.record(
            _audit_event(
                AuditEventType.STAFF_ACCOUNT_UPDATED, actor,
                resource_type="user", resource_id=user_id, details={"changed": sorted(changes)},
            )
        )
        self._uow.commit()
        return self._directory.get_staff(user_id)

    # --- mothers -----------------------------------------------------------------

    def list_midwives(self) -> list[MidwifeOption]:
        return self._directory.list_listed_midwives()

    def my_midwife(self, patient_id: uuid.UUID) -> MidwifeOption | None:
        assignment = self._assignments.active_for_patient(patient_id, CareRole.MIDWIFE)
        if assignment is None:
            return None
        profile = self._profiles.get(assignment.staff_id)
        return MidwifeOption(profile.user_id, profile.first_name, profile.last_name, profile.bio)

    def choose_midwife(self, actor: Actor, midwife_id: uuid.UUID) -> MidwifeOption:
        """The mother chooses (or changes) her midwife from the listed midwives."""
        chosen = next((m for m in self.list_midwives() if m.id == midwife_id), None)
        if chosen is None:
            raise ValidationError(
                "Choose a midwife from the list.", details={"field": "midwife_id"}
            )
        current = self._assignments.active_for_patient(actor.user_id, CareRole.MIDWIFE)
        if current is not None and current.staff_id == midwife_id:
            return chosen
        now = self._now()
        if current is not None:
            current.end(now)
            self._assignments.save(current)
        self._assignments.add(
            CareAssignment(actor.user_id, midwife_id, CareRole.MIDWIFE, started_at=now)
        )
        self._audit.record(
            _audit_event(
                AuditEventType.MIDWIFE_CHOSEN, actor, patient_id=actor.user_id,
                resource_type="user", resource_id=midwife_id,
            )
        )
        self._uow.commit()
        return chosen


class CareTeamService:
    """What the care team may see: patient lists, record access and red alerts."""

    def __init__(
        self,
        *,
        assignments: CareAssignmentRepository,
        alerts: AlertRepository,
        patients: PatientDirectory,
        audit: AuditTrail,
        uow: UnitOfWork,
        doctor_scope: DoctorPatientScope = DoctorPatientScope.ALL,
        now: Callable[[], datetime] = _utcnow,
    ):
        self._assignments = assignments
        self._alerts = alerts
        self._patients = patients
        self._audit = audit
        self._uow = uow
        self._doctor_scope = doctor_scope
        self._now = now

    # --- access ------------------------------------------------------------------

    def require_record_access(self, actor: Actor, patient_id: uuid.UUID) -> None:
        """Call before showing or changing a mother's record. A refusal is written to the audit log."""
        if not self._patients.is_patient(patient_id):
            raise NotFoundError("Patient not found.")
        if not self._can_open(actor, patient_id):
            self._deny(actor, patient_id, "record")

    def record_viewed(
        self, actor: Actor, patient_id: uuid.UUID, resource: str, resource_id: object = None
    ) -> None:
        self._audit.record(
            _audit_event(
                AuditEventType.RECORD_VIEWED, actor, patient_id=patient_id,
                resource_type=resource, resource_id=resource_id or patient_id,
            )
        )
        self._uow.commit()

    def midwife_of(self, patient_id: uuid.UUID) -> uuid.UUID | None:
        assignment = self._assignments.active_for_patient(patient_id, CareRole.MIDWIFE)
        return assignment.staff_id if assignment else None

    def list_patients(self, actor: Actor) -> list[PatientRow]:
        if actor.role == UserRole.MIDWIFE:
            return self._patients.list_patients(staff_id=actor.user_id, role=CareRole.MIDWIFE)
        if actor.role == UserRole.DOCTOR:
            if self._doctor_scope is DoctorPatientScope.ALL:
                return self._patients.list_patients()
            return self._patients.list_patients(staff_id=actor.user_id, role=CareRole.DOCTOR)
        raise PermissionDeniedError("Only doctors and midwives have a patient list.")

    # --- alerts ------------------------------------------------------------------

    def raise_alert(self, patient_id: uuid.UUID, kind: AlertKind, daily_log_id: uuid.UUID) -> None:
        """Called by the monitoring module; the caller's unit of work commits."""
        self._alerts.add(Alert(patient_id, kind, created_at=self._now(), daily_log_id=daily_log_id))

    def alert_inbox(self, actor: Actor) -> list[AlertView]:
        """A midwife sees her mothers' alerts; admins see alerts from mothers with no midwife."""
        if actor.role == UserRole.MIDWIFE:
            return self._alerts.open_for_midwife(actor.user_id)
        if actor.role == UserRole.ADMIN:
            return self._alerts.open_unassigned()
        raise PermissionDeniedError("Alerts are shown to midwives and admins.")

    def mark_alert_seen(self, actor: Actor, alert_id: uuid.UUID) -> None:
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise NotFoundError("Alert not found.")
        midwife_id = self.midwife_of(alert.patient_id)
        allowed = (actor.role == UserRole.MIDWIFE and midwife_id == actor.user_id) or (
            actor.role == UserRole.ADMIN and alert_goes_to_admins(midwife_id)
        )
        if not allowed:
            self._deny(actor, alert.patient_id, "alert")
        alert.mark_seen(actor.user_id, self._now())
        self._alerts.save(alert)
        self._audit.record(
            _audit_event(
                AuditEventType.ALERT_SEEN, actor, patient_id=alert.patient_id,
                resource_type="alert", resource_id=alert.id,
            )
        )
        self._uow.commit()

    # --- helpers -----------------------------------------------------------------

    def _can_open(self, actor: Actor, patient_id: uuid.UUID) -> bool:
        midwife = self._assignments.active_for_patient(patient_id, CareRole.MIDWIFE)
        doctor = self._assignments.active_for_patient(patient_id, CareRole.DOCTOR)
        return can_open_record(
            viewer_id=actor.user_id,
            viewer_role=actor.role,
            midwife_id=midwife.staff_id if midwife else None,
            doctor_id=doctor.staff_id if doctor else None,
            doctor_scope=self._doctor_scope,
        )

    def _deny(self, actor: Actor, patient_id: uuid.UUID, resource: str):
        self._audit.record(
            _audit_event(
                AuditEventType.ACCESS_DENIED, actor, patient_id=patient_id,
                resource_type=resource, resource_id=patient_id,
            )
        )
        # Commit before raising so the refusal is kept.
        self._uow.commit()
        raise PermissionDeniedError("This mother is not one of your patients.")


class ClinicalService:
    """The staff panel's clinical actions: notes, summary-card tags and approvals."""

    def __init__(
        self,
        *,
        access: PatientAccess,
        notes: StaffNoteRepository,
        tags: RiskTagRepository,
        approvals: ApprovalRepository,
        facts: Callable[[uuid.UUID], PatientFacts],
        audit: AuditTrail,
        uow: UnitOfWork,
        now: Callable[[], datetime] = _utcnow,
    ):
        self._access = access
        self._notes = notes
        self._tags = tags
        self._approvals = approvals
        self._facts = facts
        self._audit = audit
        self._uow = uow
        self._now = now

    # Reads below expect the caller to have checked access (see require_record_access).

    def notes(self, patient_id: uuid.UUID) -> list[NoteView]:
        return self._notes.list_for_patient(patient_id)

    def risk_tags(self, patient_id: uuid.UUID) -> list[RiskTagView]:
        added = {a.tag: a for a in self._tags.list_for_patient(patient_id)}
        derived = derive_risk_tags(self._facts(patient_id))
        views = [
            RiskTagView(tag, "staff", added[tag].note, added[tag].added_by_id)
            if tag in added else RiskTagView(tag, "record")
            for tag in RiskTag
            if tag in added or tag in derived
        ]
        return views

    def approvals(self, patient_id: uuid.UUID) -> list[ApprovalView]:
        return [
            ApprovalView(
                a.id, a.scope, a.approved_by_id, a.approved_at, a.revoked_at, a.revoked_by_id,
                a.is_active,
            )
            for a in self._approvals.list_for_patient(patient_id)
        ]

    # --- writes ------------------------------------------------------------------

    def add_note(self, actor: Actor, patient_id: uuid.UUID, body: str) -> None:
        self._access.require_record_access(actor, patient_id)
        if not body.strip():
            raise ValidationError("The note is empty.", details={"field": "body"})
        note = StaffNote(patient_id, actor.user_id, body.strip(), created_at=self._now())
        self._notes.add(note)
        self._commit(AuditEventType.RECORD_CREATED, actor, patient_id, "staff_note", note.id)

    def add_risk_tag(self, actor: Actor, patient_id: uuid.UUID, tag: RiskTag, note: str | None) -> None:
        self._access.require_record_access(actor, patient_id)
        self._tags.add(RiskTagAssignment(patient_id, tag, actor.user_id, self._now(), note))
        self._commit(AuditEventType.RECORD_UPDATED, actor, patient_id, "risk_tag", tag.value)

    def remove_risk_tag(self, actor: Actor, patient_id: uuid.UUID, tag: RiskTag) -> None:
        self._access.require_record_access(actor, patient_id)
        if not self._tags.remove(patient_id, tag):
            raise NotFoundError("This tag was not added by staff.")
        self._commit(AuditEventType.RECORD_UPDATED, actor, patient_id, "risk_tag", tag.value)

    def approve(self, actor: Actor, patient_id: uuid.UUID, scope: ApprovalScope) -> None:
        """Only doctors approve, e.g. the rehabilitation plan after the specialist visit."""
        self._require_doctor(actor)
        self._access.require_record_access(actor, patient_id)
        if self._approvals.active(patient_id, scope) is not None:
            raise ConflictError("This plan is already approved.")
        approval = CareApproval(patient_id, actor.user_id, scope, approved_at=self._now())
        self._approvals.add(approval)
        self._commit(AuditEventType.APPROVAL_GRANTED, actor, patient_id, "care_approval", approval.id)

    def revoke(self, actor: Actor, patient_id: uuid.UUID, scope: ApprovalScope) -> None:
        self._require_doctor(actor)
        self._access.require_record_access(actor, patient_id)
        approval = self._approvals.active(patient_id, scope)
        if approval is None:
            raise NotFoundError("There is no active approval to revoke.")
        approval.revoke(actor.user_id, self._now())
        self._approvals.save(approval)
        self._commit(AuditEventType.APPROVAL_REVOKED, actor, patient_id, "care_approval", approval.id)

    def _require_doctor(self, actor: Actor) -> None:
        if actor.role != UserRole.DOCTOR:
            raise PermissionDeniedError("Only doctors can approve a plan.")

    def _commit(self, event_type, actor: Actor, patient_id, resource: str, resource_id) -> None:
        self._audit.record(
            _audit_event(
                event_type, actor, patient_id=patient_id,
                resource_type=resource, resource_id=resource_id,
            )
        )
        self._uow.commit()
