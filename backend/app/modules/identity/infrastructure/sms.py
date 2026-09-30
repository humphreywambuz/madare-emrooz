"""SMS senders. A real provider (e.g. an Iranian SMS gateway) implements the same
``send(mobile, message)`` method and is selected with the SMS_BACKEND setting."""
import logging

logger = logging.getLogger(__name__)


class ConsoleSmsSender:
    """Development only: writes the message, including the code, to the log."""

    def send(self, mobile: str, message: str) -> None:
        logger.warning("SMS (console backend, not sent) to %s: %s", mobile, message)


class InMemorySmsSender:
    """Tests: keeps sent messages in a list the test can read."""

    def __init__(self, outbox: list[tuple[str, str]]):
        self.outbox = outbox

    def send(self, mobile: str, message: str) -> None:
        self.outbox.append((mobile, message))
