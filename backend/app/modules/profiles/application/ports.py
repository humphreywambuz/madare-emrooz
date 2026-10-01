import uuid
from typing import Protocol

from app.modules.profiles.domain.entities import MedicalHistory, Profile


class ProfileRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> Profile | None: ...

    def save(self, profile: Profile) -> None:
        """Insert or update. Raises ConflictError if the national code belongs to someone else."""


class MedicalHistoryRepository(Protocol):
    def get(self, user_id: uuid.UUID) -> MedicalHistory | None: ...

    def save(self, history: MedicalHistory) -> None: ...
