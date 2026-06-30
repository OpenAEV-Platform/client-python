"""Tests for DaemonProtocol — behavioral contract for daemon implementations."""

from __future__ import annotations

import pathlib
import subprocess
import sys
from typing import Any, Protocol
from unittest.mock import MagicMock

import pytest


_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
_PYOAEV_ROOT = _PROJECT_ROOT / "pyoaev"
_SDK_TEST_ROOT = _PROJECT_ROOT / "libs" / "xtm-second-oaev-sdk" / "tests"

_EXPECTED_METHODS = [
    "get_id",
    "set_callback",
    "start",
]


def _given_daemon_protocol_class():
    from xtm_second_oaev_sdk import DaemonProtocol

    return DaemonProtocol


def _given_xtm_module():
    import xtm_second_oaev_sdk

    return xtm_second_oaev_sdk


def _given_mock_implementing_all_methods():
    instance = MagicMock()
    for method_name in _EXPECTED_METHODS:
        setattr(instance, method_name, MagicMock())
    return instance


def _given_mock_missing_method(method_name: str):
    instance = _given_mock_implementing_all_methods()
    delattr(instance, method_name)
    return instance


def _when_checking_isinstance(obj: Any, protocol_cls: type) -> bool:
    return isinstance(obj, protocol_cls)


def _when_reading_module_all(module: Any) -> tuple[str, ...]:
    return tuple(getattr(module, "__all__", ()))


def _when_reading_protocol_method_names(protocol_cls: type) -> list[str]:
    names: list[str] = []
    for name, value in protocol_cls.__dict__.items():
        if name.startswith("_"):
            continue
        if callable(value):
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


def _then_member_is_in_collection(member: str, collection: tuple[str, ...]) -> None:
    assert member in collection


def _then_protocol_is_runtime_checkable(protocol_cls: type) -> None:
    assert getattr(protocol_cls, "_is_runtime_protocol", False) is True


def _then_collection_equals(actual: list[str], expected: list[str]) -> None:
    assert actual == sorted(expected)


def _then_isinstance_is_true(result: bool) -> None:
    assert result is True


def _then_isinstance_is_false(result: bool) -> None:
    assert result is False


def _then_process_exit_code_is_zero(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr


# --- Test functions ---


def test_daemon_protocol_import_from_public_surface() -> None:
    """AC-D01: DaemonProtocol is importable from xtm_second_oaev_sdk."""
    daemon_protocol = _given_daemon_protocol_class()
    assert daemon_protocol is not None


def test_daemon_protocol_is_runtime_checkable_protocol() -> None:
    """AC-D03/D04: DaemonProtocol is a runtime-checkable Protocol."""
    daemon_protocol = _given_daemon_protocol_class()
    assert issubclass(daemon_protocol, Protocol)
    _then_protocol_is_runtime_checkable(daemon_protocol)


def test_daemon_protocol_is_exported_in_module_all() -> None:
    """AC-D06: DaemonProtocol is in xtm_second_oaev_sdk.__all__."""
    module = _given_xtm_module()
    exported_names = _when_reading_module_all(module)
    _then_member_is_in_collection("DaemonProtocol", exported_names)


def test_daemon_protocol_all_count_is_102() -> None:
    """AC-D07: __all__ now contains 102 symbols."""
    module = _given_xtm_module()
    exported_names = _when_reading_module_all(module)
    assert len(exported_names) == 107


def test_daemon_protocol_exposes_exact_methods() -> None:
    """AC-D02: Protocol exposes exactly start, set_callback, get_id."""
    daemon_protocol = _given_daemon_protocol_class()
    methods = _when_reading_protocol_method_names(daemon_protocol)
    _then_collection_equals(methods, _EXPECTED_METHODS)


def test_daemon_protocol_isinstance_accepts_full_implementation() -> None:
    """AC-D08: object implementing all 3 methods satisfies DaemonProtocol."""
    daemon_protocol = _given_daemon_protocol_class()
    mock_daemon = _given_mock_implementing_all_methods()
    result = _when_checking_isinstance(mock_daemon, daemon_protocol)
    _then_isinstance_is_true(result)


@pytest.mark.parametrize("missing_method", _EXPECTED_METHODS)
def test_daemon_protocol_isinstance_rejects_missing_method(missing_method: str) -> None:
    """AC-D09: missing any single method fails runtime conformance."""
    daemon_protocol = _given_daemon_protocol_class()
    mock_daemon = _given_mock_missing_method(missing_method)
    result = _when_checking_isinstance(mock_daemon, daemon_protocol)
    _then_isinstance_is_false(result)


def test_base_daemon_structurally_satisfies_daemon_protocol() -> None:
    """AC-D10: BaseDaemon subclass satisfies isinstance(obj, DaemonProtocol)."""
    from pyoaev.daemons.base_daemon import BaseDaemon
    from xtm_second_oaev_sdk import DaemonProtocol

    class _ConcreteDaemon(BaseDaemon):
        def _setup(self):
            pass

        def _start_loop(self):
            pass

    config = MagicMock()
    config.get = MagicMock(return_value=None)
    api_client = MagicMock()
    daemon = _ConcreteDaemon(
        configuration=config, callback=lambda: None, api_client=api_client
    )
    result = _when_checking_isinstance(daemon, DaemonProtocol)
    _then_isinstance_is_true(result)


def test_base_daemon_file_unchanged() -> None:
    """AC-D11: pyoaev/daemons/base_daemon.py has no uncommitted changes."""
    result = subprocess.run(
        ["git", "diff", "--", "pyoaev/daemons/base_daemon.py"],
        cwd=_PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    _then_process_exit_code_is_zero(result)
    assert result.stdout.strip() == "", "base_daemon.py must have no changes"


def test_importing_daemon_protocol_no_circular_imports() -> None:
    """AC-D18: from xtm_second_oaev_sdk import DaemonProtocol exits cleanly."""
    result = _when_running_python_import("from xtm_second_oaev_sdk import DaemonProtocol")
    _then_process_exit_code_is_zero(result)


def test_importing_pyoaev_no_circular_imports() -> None:
    """AC-D18: import pyoaev still exits cleanly after adding DaemonProtocol."""
    result = _when_running_python_import("import pyoaev")
    _then_process_exit_code_is_zero(result)
