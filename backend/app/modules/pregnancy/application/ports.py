import uuid
from typing import Protocol

from app.modules.pregnancy.domain.entities import Pregnancy


class PregnancyRepository(Protocol):
    def get_active_for_user(self, user_id: uuid.UUID) -> Pregnancy | None: ...

    def add(self, pregnancy: Pregnancy) -> None: ...

    def save(self, pregnancy: Pregnancy) -> None: ...
