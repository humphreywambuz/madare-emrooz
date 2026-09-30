"""Enforce the dependency rules described in docs/architecture.md.

Dependencies point inwards: api -> application -> domain, and infrastructure
implements what application needs. Modules only see each other's domain and
application layers.
"""
import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
LAYERS = ("domain", "application", "infrastructure", "api")

FRAMEWORKS = ("flask", "flask_sqlalchemy", "flask_migrate", "sqlalchemy", "pydantic", "itsdangerous")
# app.wiring assembles use cases from several modules; only the api layer may use it.
FORBIDDEN_LIBS = {
    "domain": FRAMEWORKS + ("app.extensions", "app.wiring"),
    "application": FRAMEWORKS + ("app.extensions", "app.wiring"),
    "infrastructure": ("flask", "pydantic", "app.wiring"),
    "api": (),
}
FORBIDDEN_LAYERS = {
    "domain": {"application", "infrastructure", "api"},
    "application": {"infrastructure", "api"},
    "infrastructure": {"api"},
    "api": set(),
}
CROSS_MODULE_ALLOWED = {"domain", "application"}


def module_name(path: Path) -> str:
    parts = path.relative_to(APP.parent).with_suffix("").parts
    return ".".join(parts[:-1] if parts[-1] == "__init__" else parts)


def imports_of(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package = module_name(path).split(".")
    if path.name != "__init__.py":
        package = package[:-1]
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                target = ".".join(base + ([node.module] if node.module else []))
            else:
                target = node.module
            found.append(target)
            found += [f"{target}.{alias.name}" for alias in node.names]
    return found


def locate(name: str) -> tuple[str | None, str | None]:
    """Return (owner, layer) for a dotted name inside app.modules / app.shared."""
    parts = name.split(".")
    if parts[:2] == ["app", "modules"] and len(parts) >= 3:
        layer = parts[3] if len(parts) > 3 and parts[3] in LAYERS else None
        return parts[2], layer
    if parts[:2] == ["app", "shared"]:
        layer = parts[2] if len(parts) > 2 and parts[2] in LAYERS else None
        return "shared", layer
    return None, None


def source_files():
    for root in (APP / "modules", APP / "shared"):
        for path in sorted(root.rglob("*.py")):
            owner, layer = locate(module_name(path))
            if layer:
                yield pytest.param(path, owner, layer, id=str(path.relative_to(APP)))


@pytest.mark.parametrize(("path", "owner", "layer"), list(source_files()))
def test_dependency_rules(path, owner, layer):
    violations = []
    for name in imports_of(path):
        if any(name == lib or name.startswith(lib + ".") for lib in FORBIDDEN_LIBS[layer]):
            violations.append(f"{layer} must not import {name}")
            continue
        target_owner, target_layer = locate(name)
        if target_owner is None:
            continue
        if owner == "shared" and target_owner != "shared":
            violations.append(f"shared code must not import feature module {name}")
        elif target_owner == owner or target_owner == "shared":
            if target_layer in FORBIDDEN_LAYERS[layer]:
                violations.append(f"{layer} must not import {target_layer}: {name}")
        elif target_layer not in CROSS_MODULE_ALLOWED:
            violations.append(
                f"module '{owner}' may only use the domain/application layers of '{target_owner}', not {name}"
            )
    assert not violations, "\n".join(sorted(set(violations)))


def test_rules_catch_a_violation():
    """Guard against the checker silently passing everything."""
    bad = APP / "modules" / "pregnancy" / "domain" / "_tmp_bad.py"
    bad.write_text("from flask import g\nfrom ..infrastructure.models import PregnancyModel\n")
    try:
        with pytest.raises(AssertionError) as exc:
            test_dependency_rules(bad, "pregnancy", "domain")
        assert "domain must not import flask" in str(exc.value)
        assert "domain must not import infrastructure" in str(exc.value)
    finally:
        bad.unlink()
