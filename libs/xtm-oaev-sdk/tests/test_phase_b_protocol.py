"""Tests for Phase B — BaseClient Protocol abstraction."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
from typing import Any, Protocol
from unittest.mock import MagicMock

import pytest


_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
_PYOAEV_ROOT = _PROJECT_ROOT / "pyoaev"
_SDK_TEST_ROOT = _PROJECT_ROOT / "libs" / "xtm-oaev-sdk" / "tests"

_EXPECTED_METHODS = [
    "http_head",
    "http_get",
    "http_post",
    "http_patch",
    "http_put",
    "http_delete",
    "http_list",
]
_EXPECTED_PROPERTIES = [
    "per_page",
    "pagination",
    "order_by",
    "url",
    "headers",
    "ssl_verify",
    "timeout",
    "tenant_id",
    "session",
    "backend",
]
_EXPECTED_ALL_MEMBERS = _EXPECTED_METHODS + _EXPECTED_PROPERTIES
_MIXINS_BASECLIENT_LINES = [58, 81, 102, 143, 194, 228]


def _given_base_client_class():
    from xtm_oaev_sdk import BaseClient

    return BaseClient


def _given_xtm_module():
    import xtm_oaev_sdk

    return xtm_oaev_sdk


def _given_mock_implementing_all_members():
    instance = MagicMock()
    for method_name in _EXPECTED_METHODS:
        setattr(instance, method_name, MagicMock())
    for property_name in _EXPECTED_PROPERTIES:
        setattr(instance, property_name, object())
    return instance


def _given_mock_missing_member(member_name: str):
    instance = _given_mock_implementing_all_members()
    delattr(instance, member_name)
    return instance


def _given_file_lines(path: pathlib.Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _when_checking_isinstance(obj: Any, protocol_cls: type) -> bool:
    return isinstance(obj, protocol_cls)


def _when_reading_module_all(module: Any) -> tuple[str, ...]:
    return tuple(getattr(module, "__all__", ()))


def _when_reading_protocol_method_names(protocol_cls: type) -> list[str]:
    names: list[str] = []
    for name, value in protocol_cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(value, property):
            continue
        if callable(value):
            names.append(name)
    return sorted(names)


def _when_reading_protocol_property_names(protocol_cls: type) -> list[str]:
    names: list[str] = []
    for name, value in protocol_cls.__dict__.items():
        if name.startswith("_"):
            continue
        if isinstance(value, property):
            names.append(name)
    return sorted(names)


def _when_running_python_import(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=_PROJECT_ROOT,
        env={**__import__("os").environ, "PYTHONPATH": str(pathlib.Path(__file__).resolve().parents[1])},
        capture_output=True,
        text=True,
        check=False,
    )


def _when_collecting_pytest_tests(path: pathlib.Path) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", str(path)],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"collected\s+(\d+)\s+items", output)
    assert match is not None, f"Unable to parse pytest collection output:\n{output}"
    return int(match.group(1))


def _then_member_is_in_collection(member: str, collection: tuple[str, ...]) -> None:
    assert member in collection


def _then_protocol_is_runtime_checkable(protocol_cls: type) -> None:
    assert getattr(protocol_cls, "_is_runtime_protocol", False) is True


def _then_collection_equals(actual: list[str], expected: list[str]) -> None:
    assert actual == sorted(expected)


def _then_protocol_properties_are_abstract_property_members(protocol_cls: type) -> None:
    for property_name in _EXPECTED_PROPERTIES:
        descriptor = protocol_cls.__dict__.get(property_name)
        assert isinstance(descriptor, property), (
            f"{property_name} must be a @property on the Protocol"
        )


def _then_isinstance_is_true(result: bool) -> None:
    assert result is True


def _then_isinstance_is_false(result: bool) -> None:
    assert result is False


def _then_line_contains(lines: list[str], line_number: int, expected_fragment: str) -> None:
    assert expected_fragment in lines[line_number - 1]


def _then_text_does_not_contain(text: str, fragment: str) -> None:
    assert fragment not in text


def _then_process_exit_code_is_zero(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr


def _then_count_is_at_least(actual: int, threshold: int) -> None:
    assert actual >= threshold


def test_base_client_import_from_public_surface() -> None:
    """AC-B01: BaseClient is importable from xtm_oaev_sdk."""
    base_client = _given_base_client_class()
    assert base_client is not None


def test_base_client_is_runtime_checkable_protocol() -> None:
    """AC-B02: BaseClient is a runtime-checkable Protocol."""
    base_client = _given_base_client_class()
    assert issubclass(base_client, Protocol)
    _then_protocol_is_runtime_checkable(base_client)


def test_base_client_is_exported_in_module_all() -> None:
    """AC-B08: BaseClient is exported via xtm_oaev_sdk.__all__."""
    module = _given_xtm_module()
    exported_names = _when_reading_module_all(module)
    _then_member_is_in_collection("BaseClient", exported_names)


def test_base_client_protocol_exposes_exact_http_methods() -> None:
    """Protocol exposes exactly the seven required HTTP methods."""
    base_client = _given_base_client_class()
    methods = _when_reading_protocol_method_names(base_client)
    _then_collection_equals(methods, _EXPECTED_METHODS)


def test_base_client_protocol_exposes_exact_properties() -> None:
    """Protocol exposes exactly ten required data members as @property."""
    base_client = _given_base_client_class()
    properties = _when_reading_protocol_property_names(base_client)
    _then_collection_equals(properties, _EXPECTED_PROPERTIES)


def test_base_client_protocol_properties_are_abstract_properties() -> None:
    """TRAP-1: data attributes are abstract @property members, not bare attrs."""
    base_client = _given_base_client_class()
    _then_protocol_properties_are_abstract_property_members(base_client)


def test_base_client_runtime_isinstance_accepts_full_implementation() -> None:
    """AC-B03: object implementing all 17 members satisfies BaseClient."""
    base_client = _given_base_client_class()
    mock_client = _given_mock_implementing_all_members()
    result = _when_checking_isinstance(mock_client, base_client)
    _then_isinstance_is_true(result)


@pytest.mark.parametrize("missing_member", _EXPECTED_ALL_MEMBERS)
def test_base_client_runtime_isinstance_rejects_missing_single_member(missing_member: str) -> None:
    """AC-B04: missing any single required member fails runtime conformance."""
    base_client = _given_base_client_class()
    mock_client = _given_mock_missing_member(missing_member)
    result = _when_checking_isinstance(mock_client, base_client)
    _then_isinstance_is_false(result)


def test_openaev_concrete_isinstance_scenario_pending_concrete_binding() -> None:
    """AC-B05: placeholder until concrete OpenAEV/BaseClient binding exists."""
    _given_base_client_class()
    pytest.skip("Concrete OpenAEV runtime conformance check is enabled in Phase C.")


def test_base_py_no_longer_uses_openaev_annotation() -> None:
    """AC-B07: pyoaev/base.py no longer references openaev: OpenAEV annotation."""
    content = (_PYOAEV_ROOT / "base.py").read_text(encoding="utf-8")
    _then_text_does_not_contain(content, "openaev: OpenAEV")


def test_mixins_py_no_longer_uses_pyoaev_openaev_annotation() -> None:
    """AC-B06: pyoaev/mixins.py no longer references pyoaev.OpenAEV annotation."""
    content = (_PYOAEV_ROOT / "mixins.py").read_text(encoding="utf-8")
    _then_text_does_not_contain(content, "pyoaev.OpenAEV")


def test_mixins_annotations_use_base_client_on_target_lines() -> None:
    """Specific mixins.py lines now point to BaseClient annotations."""
    lines = _given_file_lines(_PYOAEV_ROOT / "mixins.py")
    for line_number in _MIXINS_BASECLIENT_LINES:
        _then_line_contains(lines, line_number, "BaseClient")


def test_base_py_removes_direct_openaev_import_if_unused() -> None:
    """BLIND-1: base.py removes OpenAEV import when only used for annotation."""
    import re
    content = (_PYOAEV_ROOT / "base.py").read_text(encoding="utf-8")
    # Check that OpenAEV is not imported as a standalone symbol (OpenAEVList is fine)
    matches = re.findall(r"import\s+OpenAEV\b(?!List)", content)
    assert not matches, f"OpenAEV still imported standalone: {matches}"


def test_mixins_py_removes_pyoaev_import_if_unused() -> None:
    """BLIND-1: mixins.py removes import pyoaev once annotations are swapped."""
    content = (_PYOAEV_ROOT / "mixins.py").read_text(encoding="utf-8")
    _then_text_does_not_contain(content, "import pyoaev")


def test_importing_base_client_does_not_trigger_circular_imports() -> None:
    """BLIND-3: from xtm_oaev_sdk import BaseClient exits cleanly."""
    result = _when_running_python_import("from xtm_oaev_sdk import BaseClient")
    _then_process_exit_code_is_zero(result)


def test_importing_pyoaev_does_not_trigger_circular_imports() -> None:
    """BLIND-3: import pyoaev exits cleanly."""
    result = _when_running_python_import("import pyoaev")
    _then_process_exit_code_is_zero(result)


def test_sdk_test_collection_count_is_at_least_119() -> None:
    """Scenario 40: SDK suite collects at least 119 tests."""
    count = _when_collecting_pytest_tests(_SDK_TEST_ROOT)
    _then_count_is_at_least(count, 119)


def test_pyoaev_test_collection_count_is_at_least_122() -> None:
    """Scenario 41: pyoaev suite collects at least 122 tests."""
    count = _when_collecting_pytest_tests(_PROJECT_ROOT / "test")
    _then_count_is_at_least(count, 122)
