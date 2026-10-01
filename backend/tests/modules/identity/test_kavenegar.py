"""The Kavenegar adapter, with the HTTP call replaced by a fake."""
import io
import json
import urllib.error
import urllib.parse

import pytest

from app import create_app
from app.config import TestConfig
from app.modules.identity.application.ports import SmsDeliveryError
from app.modules.identity.infrastructure import sms
from app.modules.identity.infrastructure.sms import KavenegarSmsSender

API_KEY = "test-api-key"


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def kavenegar_reply(status, message="تایید شد"):
    return json.dumps({"return": {"status": status, "message": message}, "entries": []}).encode()


@pytest.fixture()
def calls(monkeypatch):
    """Records each request; set ``calls.reply`` to an exception or bytes to answer with."""

    class Calls(list):
        reply = kavenegar_reply(200)

    recorded = Calls()

    def fake_urlopen(request, timeout):
        recorded.append((request, timeout))
        if isinstance(recorded.reply, Exception):
            raise recorded.reply
        return FakeResponse(recorded.reply)

    monkeypatch.setattr(sms.urllib.request, "urlopen", fake_urlopen)
    return recorded


def test_sends_the_code_with_the_verify_template(calls):
    KavenegarSmsSender(API_KEY, "madareemrooz-otp").send_login_code("+989121234567", "123456")
    (request, timeout), = calls
    assert request.full_url == f"https://api.kavenegar.com/v1/{API_KEY}/verify/lookup.json"
    assert request.get_method() == "POST" and timeout == 10
    assert urllib.parse.parse_qs(request.data.decode()) == {
        "receptor": ["09121234567"],
        "token": ["123456"],
        "template": ["madareemrooz-otp"],
    }


def test_a_rejected_message_raises_without_leaking_the_key(calls, caplog):
    calls.reply = urllib.error.HTTPError(
        "https://api.kavenegar.com/v1/…", 424, "Failed Dependency", {},
        io.BytesIO(kavenegar_reply(424, "الگو یافت نشد")),
    )
    with pytest.raises(SmsDeliveryError, match="424") as error:
        KavenegarSmsSender(API_KEY, "wrong-template").send_login_code("+989121234567", "123456")
    assert API_KEY not in str(error.value) and API_KEY not in caplog.text


@pytest.mark.parametrize("reply", [urllib.error.URLError("timed out"), TimeoutError(), b"<html>"])
def test_network_errors_and_garbage_raise(calls, reply):
    calls.reply = reply
    with pytest.raises(SmsDeliveryError):
        KavenegarSmsSender(API_KEY, "madareemrooz-otp").send_login_code("+989121234567", "1")


def test_the_app_refuses_to_start_without_an_api_key():
    class KavenegarWithoutKey(TestConfig):
        SMS_BACKEND = "kavenegar"
        KAVENEGAR_API_KEY = ""

    with pytest.raises(RuntimeError, match="KAVENEGAR_API_KEY"):
        create_app(KavenegarWithoutKey)
