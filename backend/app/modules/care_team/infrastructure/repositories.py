"""SQLAlchemy implementations of the care team ports."""
import uuid

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.modules.care_team.application.views import (
    AlertView,
    MidwifeOption,
    NoteView,
    PatientRow,
    StaffView,
)
from app.modules.care_team.domain.entities import (
    Alert,
    CareApproval,
    CareAssignment,
    RiskTagAssignment,
    StaffNote,
    StaffProfile,
)
from app.modules.care_team.domain.enums import ApprovalScope, CareRole, RiskTag
from app.modules.care_team.domain.search import PatientSearch
from app.modules.identity.domain.enums import STAFF_ROLES, UserRole
from app.shared.domain.errors import ConflictError
from app.shared.infrastructure.mapping import (
    KeyedRepository,
    constraint_name,
    copy_to_row,
    to_entity,
)

from .models import (
    AlertModel,
    CareApprovalModel,
    CareAssignmentModel,
    RiskTagAssignmentModel,
    StaffNoteModel,
    StaffProfileModel,
)

# Read-only views of other modules' tables, joined by name for the staff panel lists.
# Writes to them always go through the owning module.
_users = sa.table(
    "users",
    sa.column("id"), sa.column("mobile"), sa.column("role"), sa.column("is_active"),
    sa.column("created_at"),
)
_profiles = sa.table(
    "profiles",
    sa.column("user_id"), sa.column("first_name"), sa.column("last_name"),
    sa.column("join_goal"), sa.column("reproductive_status"), sa.column("national_code"),
)


class SqlAlchemyStaffProfileRepository(KeyedRepository[StaffProfile]):
    model = StaffProfileModel
    entity = StaffProfile


class SqlAlchemyCareAssignmentRepository:
    def __init__(self, session: Session):
        self._session = session

    def active_for_patient(self, patient_id: uuid.UUID, role: CareRole) -> CareAssignment | None:
        row = self._session.scalar(
            sa.select(CareAssignmentModel).where(
                CareAssignmentModel.patient_id == patient_id,
                CareAssignmentModel.care_role == role,
                CareAssignmentModel.ended_at.is_(None),
            )
        )
        return to_entity(CareAssignment, row) if row else None

    def active_for_staff(self, staff_id: uuid.UUID, role: CareRole) -> list[CareAssignment]:
        rows = self._session.scalars(
            sa.select(CareAssignmentModel).where(
                CareAssignmentModel.staff_id == staff_id,
                CareAssignmentModel.care_role == role,
                CareAssignmentModel.ended_at.is_(None),
            )
        )
        return [to_entity(CareAssignment, row) for row in rows]

    def add(self, assignment: CareAssignment) -> None:
        row = CareAssignmentModel()
        copy_to_row(assignment, row)
        try:
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError as exc:
            # Two requests chose a midwife at the same moment.
            if constraint_name(exc) == "uq_care_assignments_one_active_per_role":
                raise ConflictError("Your choice changed in the meantime. Please try again.") from exc
            raise

    def save(self, assignment: CareAssignment) -> None:
        copy_to_row(assignment, self._session.get(CareAssignmentModel, assignment.id))
        self._session.flush()


def _active_assignment(role: CareRole):
    return sa.and_(
        CareAssignmentModel.care_role == role, CareAssignmentModel.ended_at.is_(None)
    )


class SqlAlchemyAlertRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, alert: Alert) -> None:
        row = AlertModel()
        copy_to_row(alert, row)
        self._session.add(row)
        self._session.flush()

    def get(self, alert_id: uuid.UUID) -> Alert | None:
        row = self._session.get(AlertModel, alert_id)
        return to_entity(Alert, row) if row else None

    def save(self, alert: Alert) -> None:
        copy_to_row(alert, self._session.get(AlertModel, alert.id))
        self._session.flush()

    def _open_alerts(self):
        return (
            sa.select(
                AlertModel.id, AlertModel.kind, AlertModel.created_at, AlertModel.seen_at,
                AlertModel.patient_id, _profiles.c.first_name, _profiles.c.last_name,
                _users.c.mobile,
            )
            .join(_users, _users.c.id == AlertModel.patient_id)
            .outerjoin(_profiles, _profiles.c.user_id == AlertModel.patient_id)
            .where(AlertModel.seen_at.is_(None))
            .order_by(AlertModel.created_at.desc())
        )

    def _views(self, query) -> list[AlertView]:
        return [
            AlertView(
                id=r.id, kind=r.kind, created_at=r.created_at, seen_at=r.seen_at,
                patient_id=r.patient_id, patient_first_name=r.first_name,
                patient_last_name=r.last_name, patient_mobile=r.mobile,
            )
            for r in self._session.execute(query)
        ]

    def open_for_midwife(self, midwife_id: uuid.UUID) -> list[AlertView]:
        query = self._open_alerts().join(
            CareAssignmentModel,
            sa.and_(
                CareAssignmentModel.patient_id == AlertModel.patient_id,
                _active_assignment(CareRole.MIDWIFE),
                CareAssignmentModel.staff_id == midwife_id,
            ),
        )
        return self._views(query)

    def open_unassigned(self) -> list[AlertView]:
        has_midwife = (
            sa.select(CareAssignmentModel.id)
            .where(
                CareAssignmentModel.patient_id == AlertModel.patient_id,
                _active_assignment(CareRole.MIDWIFE),
            )
            .exists()
        )
        return self._views(self._open_alerts().where(~has_midwife))


class SqlAlchemyStaffDirectory:
    def __init__(self, session: Session):
        self._session = session

    def _query(self):
        return (
            sa.select(
                _users.c.id, _users.c.role, _users.c.mobile, _users.c.is_active,
                StaffProfileModel.first_name, StaffProfileModel.last_name, StaffProfileModel.bio,
                StaffProfileModel.is_listed,
            )
            .select_from(_users)
            .outerjoin(StaffProfileModel, StaffProfileModel.user_id == _users.c.id)
            .where(_users.c.role.in_([r.value for r in STAFF_ROLES]))
            .order_by(_users.c.role, StaffProfileModel.last_name, StaffProfileModel.first_name)
        )

    @staticmethod
    def _view(r) -> StaffView:
        return StaffView(
            user_id=r.id, role=r.role, mobile=r.mobile, first_name=r.first_name,
            last_name=r.last_name, bio=r.bio, is_listed=bool(r.is_listed), is_active=r.is_active,
        )

    def get_staff(self, user_id: uuid.UUID) -> StaffView | None:
        row = self._session.execute(self._query().where(_users.c.id == user_id)).first()
        return self._view(row) if row else None

    def list_staff(self) -> list[StaffView]:
        return [self._view(r) for r in self._session.execute(self._query())]

    def list_listed_midwives(self) -> list[MidwifeOption]:
        query = self._query().where(
            _users.c.role == UserRole.MIDWIFE.value,
            _users.c.is_active.is_(True),
            StaffProfileModel.is_listed.is_(True),
        )
        return [
            MidwifeOption(r.id, r.first_name, r.last_name, r.bio)
            for r in self._session.execute(query)
        ]


class SqlAlchemyPatientDirectory:
    def __init__(self, session: Session):
        self._session = session

    def is_patient(self, user_id: uuid.UUID) -> bool:
        return bool(
            self._session.scalar(
                sa.select(sa.literal(True)).where(
                    _users.c.id == user_id, _users.c.role == UserRole.USER.value
                )
            )
        )

    def list_patients(
        self,
        *,
        staff_id: uuid.UUID | None = None,
        role: CareRole | None = None,
        search: PatientSearch | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[PatientRow], int]:
        midwife = aliased(CareAssignmentModel)
        open_alerts = (
            sa.select(
                AlertModel.patient_id,
                sa.func.count().label("open_alerts"),
                sa.func.max(AlertModel.created_at).label("last_alert_at"),
            )
            .where(AlertModel.seen_at.is_(None))
            .group_by(AlertModel.patient_id)
            .subquery()
        )
        query = (
            sa.select(
                _users.c.id, _users.c.mobile, _profiles.c.first_name, _profiles.c.last_name,
                _profiles.c.join_goal, _profiles.c.reproductive_status,
                midwife.staff_id.label("midwife_id"),
                sa.func.coalesce(open_alerts.c.open_alerts, 0).label("open_alerts"),
                open_alerts.c.last_alert_at,
            )
            .select_from(_users)
            .outerjoin(_profiles, _profiles.c.user_id == _users.c.id)
            .outerjoin(
                midwife,
                sa.and_(
                    midwife.patient_id == _users.c.id,
                    midwife.care_role == CareRole.MIDWIFE,
                    midwife.ended_at.is_(None),
                ),
            )
            .outerjoin(open_alerts, open_alerts.c.patient_id == _users.c.id)
            .where(_users.c.role == UserRole.USER.value)
            .order_by(
                sa.desc("open_alerts"),
                open_alerts.c.last_alert_at.desc().nulls_last(),
                _users.c.created_at.desc(),
            )
        )
        if staff_id is not None:
            assigned = (
                sa.select(CareAssignmentModel.id)
                .where(
                    CareAssignmentModel.patient_id == _users.c.id,
                    CareAssignmentModel.staff_id == staff_id,
                    _active_assignment(role),
                )
                .exists()
            )
            query = query.where(assigned)
        if search is not None:
            query = query.where(*_search_conditions(search))
        total = self._session.scalar(
            sa.select(sa.func.count()).select_from(query.order_by(None).subquery())
        )
        page_query = query.limit(per_page).offset((page - 1) * per_page)
        return [PatientRow(**r._mapping) for r in self._session.execute(page_query)], total


def _normalised(column):
    """Lower-case, with Arabic ي/ك read as Persian ی/ک, so either spelling matches."""
    return sa.func.lower(sa.func.translate(sa.func.coalesce(column, ""), "يكى", "یکی"))


def _search_conditions(search: PatientSearch) -> list:
    if search.digits:
        pattern = f"%{search.digits}%"
        return [sa.or_(_users.c.mobile.like(pattern), _profiles.c.national_code.like(pattern))]
    names = sa.func.concat(_normalised(_profiles.c.first_name), " ", _normalised(_profiles.c.last_name))
    # Every word must appear somewhere in her name; LIKE wildcards in the input are literal.
    return [
        names.like("%" + w.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
        for w in search.words
    ]


class SqlAlchemyApprovalRepository:
    def __init__(self, session: Session):
        self._session = session

    def active(self, patient_id: uuid.UUID, scope: ApprovalScope) -> CareApproval | None:
        row = self._session.scalar(
            sa.select(CareApprovalModel).where(
                CareApprovalModel.patient_id == patient_id,
                CareApprovalModel.scope == scope,
                CareApprovalModel.revoked_at.is_(None),
            )
        )
        return to_entity(CareApproval, row) if row else None

    def list_for_patient(self, patient_id: uuid.UUID) -> list[CareApproval]:
        rows = self._session.scalars(
            sa.select(CareApprovalModel)
            .where(CareApprovalModel.patient_id == patient_id)
            .order_by(CareApprovalModel.approved_at.desc())
        )
        return [to_entity(CareApproval, row) for row in rows]

    def add(self, approval: CareApproval) -> None:
        row = CareApprovalModel()
        copy_to_row(approval, row)
        try:
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError as exc:
            if constraint_name(exc) == "uq_care_approvals_one_active_per_scope":
                raise ConflictError("This plan is already approved.") from exc
            raise

    def save(self, approval: CareApproval) -> None:
        copy_to_row(approval, self._session.get(CareApprovalModel, approval.id))
        self._session.flush()


class SqlAlchemyStaffNoteRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, note: StaffNote) -> None:
        row = StaffNoteModel()
        copy_to_row(note, row)
        self._session.add(row)
        self._session.flush()

    def list_for_patient(self, patient_id: uuid.UUID) -> list[NoteView]:
        query = (
            sa.select(
                StaffNoteModel.id, StaffNoteModel.body, StaffNoteModel.created_at,
                StaffNoteModel.author_id, StaffProfileModel.first_name, StaffProfileModel.last_name,
                _users.c.role,
            )
            .join(_users, _users.c.id == StaffNoteModel.author_id)
            .outerjoin(StaffProfileModel, StaffProfileModel.user_id == StaffNoteModel.author_id)
            .where(StaffNoteModel.patient_id == patient_id)
            .order_by(StaffNoteModel.created_at.desc())
        )
        return [
            NoteView(
                id=r.id, body=r.body, created_at=r.created_at, author_id=r.author_id,
                author_name=" ".join(filter(None, (r.first_name, r.last_name))) or None,
                author_role=r.role,
            )
            for r in self._session.execute(query)
        ]


class SqlAlchemyRiskTagRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_for_patient(self, patient_id: uuid.UUID) -> list[RiskTagAssignment]:
        rows = self._session.scalars(
            sa.select(RiskTagAssignmentModel).where(RiskTagAssignmentModel.patient_id == patient_id)
        )
        return [to_entity(RiskTagAssignment, row) for row in rows]

    def add(self, assignment: RiskTagAssignment) -> None:
        row = RiskTagAssignmentModel()
        copy_to_row(assignment, row)
        try:
            with self._session.begin_nested():
                self._session.add(row)
        except IntegrityError as exc:
            if constraint_name(exc) == "uq_risk_tag_per_patient":
                raise ConflictError("This tag is already on her summary card.") from exc
            raise

    def remove(self, patient_id: uuid.UUID, tag: RiskTag) -> bool:
        result = self._session.execute(
            sa.delete(RiskTagAssignmentModel).where(
                RiskTagAssignmentModel.patient_id == patient_id, RiskTagAssignmentModel.tag == tag
            )
        )
        return result.rowcount > 0
