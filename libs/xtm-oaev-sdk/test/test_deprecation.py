"""Tests for the reusable PEP 562 module-deprecation factory.

Covers the exact pattern the legacy modules hand-roll: a ``{old: (msg, target)}``
mapping driving a module ``__getattr__`` that warns and returns the *same*
object, preserves identity (no wrapper), and still raises on genuine misses.
"""

import sys
import types
import warnings

import pytest
from xtm_oaev_sdk import make_deprecated_getattr


# --- sentinel: a real object the deprecated name should alias, exactly ---
class _Sentinel:
    pass


_TARGET = _Sentinel()


def _install_module(name, mapping, *, module_name=None):
    """Create a bare module that uses the factory as its PEP 562 ``__getattr__``."""
    mod = types.ModuleType(name)
    mod.__getattr__ = make_deprecated_getattr(mapping, module_name=module_name or name)
    sys.modules[name] = mod
    return mod


def _capture(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = fn()
    return result, caught


# --- 1. the core contract: warn once per access + return the exact object ---
def test_deprecated_access_warns_and_preserves_identity() -> None:
    mod = _install_module("tdep_ident", {"Old": ("Use 'new' instead.", _TARGET)})
    try:
        result, caught = _capture(lambda: mod.Old)
    finally:
        sys.modules.pop("tdep_ident", None)

    assert result is _TARGET, "the shim must return the exact object, not a wrapper"
    assert len(caught) == 1
    assert isinstance(caught[0].message, DeprecationWarning)
    assert str(caught[0].message) == "Use 'new' instead."


# --- 2. repeated access keeps returning the same object ---
def test_repeated_access_is_stable() -> None:
    mod = _install_module("tdep_repeat", {"Old": ("msg", _TARGET)})
    try:
        first = mod.Old
        second = mod.Old
    finally:
        sys.modules.pop("tdep_repeat", None)
    assert first is _TARGET
    assert second is _TARGET


# --- 3. a real `from <module> import <old>` triggers the shim ---
def test_from_import_triggers_deprecation() -> None:
    _install_module("tdep_fromimp", {"Old": ("moved", _TARGET)})
    try:
        namespace: dict = {}
        result, caught = _capture(
            lambda: exec("from tdep_fromimp import Old as _got", namespace)
        )
        assert namespace["_got"] is _TARGET
        assert any(isinstance(w.message, DeprecationWarning) for w in caught)
    finally:
        sys.modules.pop("tdep_fromimp", None)


# --- 4. a name that is NOT deprecated must still raise AttributeError ---
def test_unknown_name_raises_attribution_error() -> None:
    mod = _install_module(
        "tdep_miss", {"Old": ("moved", _TARGET)}, module_name="tdep_miss"
    )
    try:
        with pytest.raises(AttributeError) as exc:
            _capture(lambda: mod.DoesNotExist)
        assert "tdep_miss" in str(exc.value)
        assert "DoesNotExist" in str(exc.value)
    finally:
        sys.modules.pop("tdep_miss", None)


# --- 5. a `from` import of an unknown name surfaces as ImportError ---
def test_from_import_of_missing_name_raises_import_error() -> None:
    _install_module("tdep_miss2", {"Old": ("moved", _TARGET)})
    try:
        with pytest.raises(ImportError):
            _capture(lambda: exec("from tdep_miss2 import Nope", {}))
    finally:
        sys.modules.pop("tdep_miss2", None)


# --- 6. the factory validates its input up front (import-time failure) ---
def test_malformed_mapping_raises_value_error() -> None:
    with pytest.raises(ValueError):
        make_deprecated_getattr({123: ("msg", _TARGET)})  # non-string key
    with pytest.raises(ValueError):
        make_deprecated_getattr({"Old": "just-a-string"})  # not a 2-tuple
    with pytest.raises(ValueError):
        make_deprecated_getattr({"Old": ("only-a-message",)})  # 1-tuple


# --- 7. input mapping is copied; later mutation does not change the shim ---
def test_mapping_is_copied_not_referenced() -> None:
    mapping = {"Old": ("msg", _TARGET)}
    mod = _install_module("tdep_copy", mapping)
    try:
        mapping["Old"] = ("CHANGED", object())  # mutate the caller's mapping
        result, _ = _capture(lambda: mod.Old)
        assert result is _TARGET
        assert str(_[0].message) == "msg"
    finally:
        sys.modules.pop("tdep_copy", None)


# --- 8. the primitive is a public, documented export ---
def test_public_export_and_all() -> None:
    import xtm_oaev_sdk as sdk

    assert sdk.make_deprecated_getattr is make_deprecated_getattr
    assert "make_deprecated_getattr" in sdk.__all__


# --- 9. one factory per module; modules do not interfere with each other ---
def test_two_modules_independent() -> None:
    a = _install_module("tdep_a", {"X": ("a-msg", "A")})
    b = _install_module("tdep_b", {"Y": ("b-msg", "B")})
    try:
        result, _ = _capture(lambda: (a.X, b.Y))
        assert result == ("A", "B")
        # cross-module name does not exist on the other
        with pytest.raises(AttributeError):
            a.Y
    finally:
        sys.modules.pop("tdep_a", None)
        sys.modules.pop("tdep_b", None)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-v"]))
