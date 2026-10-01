"""Startup checks and reverse-proxy handling."""
import pytest

from app import create_app
from app.config import TestConfig


def test_real_sms_needs_a_real_secret_key():
    class Weak(TestConfig):
        SMS_BACKEND = "kavenegar"
        KAVENEGAR_API_KEY = "key"
        SECRET_KEY = "change-me"

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(Weak)

    class Strong(Weak):
        SECRET_KEY = "x" * 48

    create_app(Strong)


def test_trusted_proxy_count_reads_the_forwarded_address():
    from flask import request

    class BehindNginx(TestConfig):
        TRUSTED_PROXY_COUNT = 1

    app = create_app(BehindNginx)

    @app.get("/_ip")
    def _ip():
        return request.remote_addr

    with app.test_client() as c:
        seen = c.get("/_ip", environ_base={"REMOTE_ADDR": "127.0.0.1"}, headers={"X-Forwarded-For": "203.0.113.7"})
        assert seen.get_data(as_text=True) == "203.0.113.7"

    plain = create_app(TestConfig)

    @plain.get("/_ip")
    def _ip2():
        return request.remote_addr

    with plain.test_client() as c:
        # Without a trusted proxy the header is ignored, so clients can't fake their address.
        seen = c.get("/_ip", environ_base={"REMOTE_ADDR": "198.51.100.1"}, headers={"X-Forwarded-For": "203.0.113.7"})
        assert seen.get_data(as_text=True) == "198.51.100.1"
