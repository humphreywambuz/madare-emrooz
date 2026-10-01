"""The Postman collection (docs/postman) must cover every route and be up to date."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_postman.py"


def load_generator():
    spec = importlib.util.spec_from_file_location("generate_postman", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_route_is_in_the_collection(app):
    generator = load_generator()
    routes = {
        (method, rule.rule)
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    documented = set(generator.endpoints())
    assert routes - documented == set(), "add these to scripts/generate_postman.py"
    assert documented - routes == set(), "these no longer exist"


def test_committed_files_are_current():
    generator = load_generator()
    assert generator.COLLECTION.read_text(encoding="utf-8") == generator.render(generator.build_collection()), (
        "run python scripts/generate_postman.py"
    )
    assert generator.ENVIRONMENT.read_text(encoding="utf-8") == generator.render(generator.build_environment())
