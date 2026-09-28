from flask import Flask

from .config import Config
from .extensions import db, migrate


def create_app(config_class: type[Config] = Config) -> Flask:
    """Composition root: wires configuration, extensions, modules and error handling."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from .modules import register_blueprints, register_models
    from .shared.api.errors import register_error_handlers

    register_models()
    register_blueprints(app)
    register_error_handlers(app)

    return app
