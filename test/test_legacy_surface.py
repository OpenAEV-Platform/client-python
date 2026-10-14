"""Legacy surface guard: the SDK split must never break existing code.

Every public name the released pyoaev exposed (recorded in
``fixtures/legacy_surface.json`` by ``generate_legacy_surface.py``) must still
resolve from the same module, possibly through a deprecation shim.
"""

import importlib
import json
import warnings
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "legacy_surface.json"


def _given_legacy_surface() -> dict[str, Any]:
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _given_legacy_names() -> list[tuple[str, str]]:
    modules = _given_legacy_surface()["modules"]
    return [(module, name) for module, names in modules.items() for name in names]


def _when_importing_module(module: str) -> ModuleType:
    return importlib.import_module(module)


def _when_resolving_name(module: ModuleType, name: str) -> bool:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            getattr(module, name)
        except AttributeError:
            return False
    return True


def _then_name_resolves(resolved: bool, module: str, name: str) -> None:
    assert resolved, (
        f"'{module}.{name}' no longer resolves: legacy code importing it breaks. "
        "Serve it from the module's deprecation shim."
    )


def test_golden_records_a_released_pyoaev() -> None:
    """It pins the surface of a released pyoaev version."""
    surface = _given_legacy_surface()
    assert surface["pyoaev_version"]
    assert surface["modules"]["pyoaev"]


@pytest.mark.parametrize("module", sorted(_given_legacy_surface()["modules"]))
def test_every_legacy_module_still_imports(module: str) -> None:
    """It keeps every legacy module importable."""
    assert _when_importing_module(module).__name__ == module


@pytest.mark.parametrize(("module", "name"), _given_legacy_names())
def test_every_legacy_name_still_resolves(module: str, name: str) -> None:
    """It keeps every legacy name reachable from its original module."""
    resolved = _when_resolving_name(_when_importing_module(module), name)
    _then_name_resolves(resolved, module, name)
