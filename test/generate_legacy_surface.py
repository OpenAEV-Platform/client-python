"""Record the public surface of an installed pyoaev release.

The legacy surface guard (``test_legacy_surface.py``) asserts that every name a
released pyoaev exposed still resolves, so the SDK split never breaks existing
code. Regenerate the golden from the *released* package, never from the
working tree::

    python -m venv /tmp/pyoaev-release
    /tmp/pyoaev-release/bin/pip install "pyoaev==<version>"
    /tmp/pyoaev-release/bin/python test/generate_legacy_surface.py

A public name is anything in a module's ``__all__``, any class or function
defined in pyoaev (including re-exports from other pyoaev modules), and any
upper-case data constant.
"""

import importlib
import json
import pkgutil
import types
import warnings
from pathlib import Path

import pyoaev

GOLDEN_PATH = Path(__file__).parent / "fixtures" / "legacy_surface.json"

_DATA_CONSTANT_TYPES = (str, int, float, list, tuple, dict)


def _is_public(name: str, obj: object, exported: set[str]) -> bool:
    if name in exported:
        return True
    if name.startswith("_") or isinstance(obj, types.ModuleType):
        return False
    if (getattr(obj, "__module__", None) or "").startswith("pyoaev"):
        return True
    is_data = isinstance(obj, _DATA_CONSTANT_TYPES) and not isinstance(obj, bool)
    return name.isupper() and is_data


def _public_names(module: types.ModuleType) -> list[str]:
    exported = set(getattr(module, "__all__", ()))
    names = []
    for name in dir(module):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            obj = getattr(module, name, None)
        if _is_public(name, obj, exported):
            names.append(name)
    return sorted(names)


def main() -> None:
    modules = {"pyoaev": _public_names(pyoaev)}
    for info in pkgutil.walk_packages(pyoaev.__path__, "pyoaev."):
        modules[info.name] = _public_names(importlib.import_module(info.name))
    surface = {"pyoaev_version": pyoaev.__version__, "modules": modules}
    GOLDEN_PATH.write_text(json.dumps(surface, indent=2, sort_keys=True) + "\n")
    print(f"wrote {GOLDEN_PATH}")


if __name__ == "__main__":
    main()
