from flask import Flask

from .config import Config
from .extensions import db, migrate
from .shared.api.json import IsoJSONProvider


class App(Flask):
    json_provider_class = IsoJSONProvider


def create_app(config_class: type[Config] = Config) -> Flask:
    """Composition root: wires configuration, extensions, modules and error handling."""
    app = App(__name__)
    app.config.from_object(config_class)
    if app.config["SMS_BACKEND"] == "kavenegar" and not app.config["KAVENEGAR_API_KEY"]:
        # Fail at startup rather than on the first sign-in.
        raise RuntimeError("SMS_BACKEND is kavenegar but KAVENEGAR_API_KEY is not set.")

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

    return app
