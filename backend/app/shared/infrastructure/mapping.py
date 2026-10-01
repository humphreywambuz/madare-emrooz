"""Copy fields between domain dataclasses and ORM rows, and save them."""
import dataclasses
from collections.abc import Mapping
from typing import Generic, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.shared.domain.errors import ConflictError

E = TypeVar("E")


def entity_fields(entity_cls) -> tuple[str, ...]:
    return tuple(f.name for f in dataclasses.fields(entity_cls))


def to_entity(entity_cls: type[E], row) -> E:
    return entity_cls(**{f: getattr(row, f) for f in entity_fields(entity_cls)})


def copy_to_row(entity, row) -> None:
    for f in entity_fields(type(entity)):
        setattr(row, f, getattr(entity, f))


def constraint_name(error: IntegrityError) -> str | None:
    return getattr(getattr(error.orig, "diag", None), "constraint_name", None)


class KeyedRepository(Generic[E]):
    """A repository for an entity stored as one row per key (e.g. one profile per user).

    ``conflicts`` maps unique constraint names to the message of the ConflictError
    raised when a save breaks them.
    """

    model: type
    entity: type[E]
    key: str = "user_id"
    conflicts: Mapping[str, str] = {}

    def __init__(self, session: Session):
        self._session = session

    def get(self, key) -> E | None:
        row = self._session.get(self.model, key)
        return to_entity(self.entity, row) if row else None

    def save(self, entity: E) -> None:
        """Insert or update. A savepoint keeps the session usable if the database refuses it."""
        try:
            with self._session.begin_nested():
                row = self._session.get(self.model, getattr(entity, self.key))
                if row is None:
                    row = self.model()
                    self._session.add(row)
                copy_to_row(entity, row)
        except IntegrityError as exc:
            message = self.conflicts.get(constraint_name(exc))
            if message:
                raise ConflictError(message) from exc
            raise
