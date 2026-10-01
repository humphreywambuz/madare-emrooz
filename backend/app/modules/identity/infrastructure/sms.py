"""SMS senders, selected with the SMS_BACKEND setting (see ``app.wiring.sms_sender``)."""
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

from app.modules.identity.application.ports import SmsDeliveryError

logger = logging.getLogger(__name__)


class ConsoleSmsSender:
    """Development only: writes the message, including the code, to the log."""

    def __init__(self, template: str):
        self._template = template

    def send_login_code(self, mobile: str, code: str) -> None:
        logger.warning(
            "SMS (console backend, not sent) to %s: %s", mobile, self._template.format(code=code)
        )


class InMemorySmsSender:
    """Tests: keeps sent messages in a list the test can read."""

    def __init__(self, outbox: list[tuple[str, str]], template: str):
        self.outbox = outbox
        self._template = template

    def send_login_code(self, mobile: str, code: str) -> None:
        self.outbox.append((mobile, self._template.format(code=code)))


class KavenegarSmsSender:
    """Sends the code with Kavenegar's Verify Lookup API.

    The message text is the template defined in the Kavenegar panel; it contains ``%token``,
    which Kavenegar replaces with the code. The API key is part of the URL, so the URL is never
    logged or put in an error message.
    """

    BASE_URL = "https://api.kavenegar.com/v1"

    def __init__(self, api_key: str, template: str, *, timeout_seconds: float = 10):
        if not api_key:
            raise ValueError("KAVENEGAR_API_KEY is not set.")
        if not template:
            raise ValueError("KAVENEGAR_OTP_TEMPLATE is not set.")
        self._api_key = api_key
        self._template = template
        self._timeout = timeout_seconds

    def send_login_code(self, mobile: str, code: str) -> None:
        url = f"{self.BASE_URL}/{self._api_key}/verify/lookup.json"
        body = urllib.parse.urlencode(
            {"receptor": _local_form(mobile), "token": code, "template": self._template}
        ).encode()
        request = urllib.request.Request(url, data=body, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:
                payload = response.read()
        except urllib.error.HTTPError as error:
            # Kavenegar answers errors with an HTTP status and a JSON body (e.g. 424: unknown template).
            payload = error.read()
        except (urllib.error.URLError, TimeoutError) as error:
            logger.error("Kavenegar request failed: %s", type(error).__name__)
            raise SmsDeliveryError("Kavenegar could not be reached.") from None

        status, message = _parse_result(payload)
        if status != 200:
            logger.error("Kavenegar rejected the message: status %s, %s", status, message)
            raise SmsDeliveryError(f"Kavenegar returned status {status}.")


def _local_form(mobile: str) -> str:
    """+989121234567 -> 09121234567, the form Kavenegar documents for receptors."""
    return "0" + mobile.removeprefix("+98") if mobile.startswith("+98") else mobile


def _parse_result(payload: bytes) -> tuple[int | None, str]:
    try:
        result = json.loads(payload)["return"]
        return int(result["status"]), str(result.get("message", ""))
    except (ValueError, KeyError, TypeError):
        return None, "unreadable response"
