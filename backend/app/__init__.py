from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import DEVELOPMENT_SECRET_KEYS, Config
from .extensions import db, migrate
from .shared.api.json import IsoJSONProvider


class App(Flask):
    json_provider_class = IsoJSONProvider


def create_app(config_class: type[Config] = Config) -> Flask:
    """Composition root: wires configuration, extensions, modules and error handling."""
    app = App(__name__)
    app.config.from_object(config_class)
    _check_settings(app)
    proxies = app.config["TRUSTED_PROXY_COUNT"]
    if proxies:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxies, x_proto=proxies, x_host=proxies)

    db.init_app(app)
    migrate.init_app(app, db)

    from .modules import register_blueprints, register_models
    from .modules.identity.infrastructure.user_status import is_user_active
    from .shared.api.auth import register_user_status_check
    from .shared.api.errors import register_error_handlers

    register_models()
    register_blueprints(app)
    register_error_handlers(app)
    register_user_status_check(app, is_user_active)

    from .cli import register_commands

    register_commands(app)

    return app


def _check_settings(app: Flask) -> None:
    """Fail at startup rather than on the first request."""
    if app.config["SMS_BACKEND"] == "kavenegar":
        if not app.config["KAVENEGAR_API_KEY"]:
            raise RuntimeError("SMS_BACKEND is kavenegar but KAVENEGAR_API_KEY is not set.")
        # Real SMS means real users: the key signing tokens and partner links must be secret.
        if app.config["SECRET_KEY"] in DEVELOPMENT_SECRET_KEYS or len(app.config["SECRET_KEY"]) < 32:
            raise RuntimeError("Set SECRET_KEY to a random value of at least 32 characters.")
