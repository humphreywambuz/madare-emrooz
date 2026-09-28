from typing import Protocol


class UnitOfWork(Protocol):
    """Transaction boundary for a use case."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
