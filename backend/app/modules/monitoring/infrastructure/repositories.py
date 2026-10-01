import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.modules.monitoring.domain.entities import DailyLog
from app.shared.infrastructure.mapping import copy_to_row, to_entity

from .models import DailyLogModel


class SqlAlchemyDailyLogRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, log: DailyLog) -> None:
        row = DailyLogModel()
        copy_to_row(log, row)
        self._session.add(row)
        self._session.flush()

    def list_for_patient(self, patient_id: uuid.UUID, limit: int) -> list[DailyLog]:
        rows = self._session.scalars(
            sa.select(DailyLogModel)
            .where(DailyLogModel.patient_id == patient_id)
            .order_by(DailyLogModel.recorded_at.desc())
            .limit(limit)
        )
        return [to_entity(DailyLog, row) for row in rows]
