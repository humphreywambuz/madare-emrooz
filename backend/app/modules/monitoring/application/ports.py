import uuid
from typing import Protocol

from app.modules.monitoring.domain.entities import DailyLog


class DailyLogRepository(Protocol):
    def add(self, log: DailyLog) -> None: ...

    def list_for_patient(self, patient_id: uuid.UUID, limit: int) -> list[DailyLog]:
        """Newest first."""
