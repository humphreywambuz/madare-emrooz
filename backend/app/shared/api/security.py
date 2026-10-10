"""Content-Security-Policy for what the API itself serves.

JSON and file downloads are never meant to be shown as a page, so by default nothing may load,
run or frame them. A page the API renders (the partner QR page) sets its own, narrower policy.
"""
from flask import Flask

API_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def _content_security_policy(response):
        response.headers.setdefault("Content-Security-Policy", API_POLICY)
        return response
