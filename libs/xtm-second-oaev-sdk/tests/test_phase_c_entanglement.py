"""Tests for Phase C — entanglement guards and cross-cutting concerns."""

import importlib
import pathlib
import re
from typing import Any

import pytest


_CLIENT_PYTHON_ROOT = pathlib.Path(__file__).resolve().parents[3]
_SDK_ROOT = _CLIENT_PYTHON_ROOT / "libs" / "xtm-second-oaev-sdk" / "xtm_second_oaev_sdk"
_SDK_TREE_ROOT = _CLIENT_PYTHON_ROOT / "libs" / "xtm-oaev-sdk"
_PYOAEV_ROOT = _CLIENT_PYTHON_ROOT / "pyoaev"


def _given_sdk_source_files() -> list[pathlib.Path]:
    return sorted(_SDK_ROOT.rglob("*.py"))


def _given_sdk_tree_files() -> list[pathlib.Path]:
    return sorted(_SDK_TREE_ROOT.rglob("*.py"))


def _given_file_content(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _when_searching_for_pattern(
    files: list[pathlib.Path], pattern: str
) -> list[tuple[pathlib.Path, str]]:
    regex = re.compile(pattern)
    matches: list[tuple[pathlib.Path, str]] = []
    for file_path in files:
        for line in _given_file_content(file_path).splitlines():
            if regex.search(line):
                matches.append((file_path, line))
    return matches


def _when_searching_in_file(path: pathlib.Path, pattern: str) -> list[str]:
    regex = re.compile(pattern)
    return [line for line in _given_file_content(path).splitlines() if regex.search(line)]


def _when_importing_helper_symbol(symbol_name: str) -> tuple[Any | None, ImportError | None]:
    try:
        helpers_module = importlib.import_module("pyoaev.helpers")
    except ImportError as import_error:
        return None, import_error
    return getattr(helpers_module, symbol_name, None), None


def _then_no_matches_found(matches: list[Any]) -> None:
    assert matches == [], f"Found unexpected matches: {matches}"


def _then_import_succeeds(error: ImportError | None, symbol_name: str) -> None:
    assert error is None, f"ImportError while importing {symbol_name}: {error}"


def _then_symbol_exists(symbol: Any, symbol_name: str) -> None:
    assert symbol is not None, f"Expected pyoaev.helpers.{symbol_name} to exist"


@pytest.mark.parametrize(
    "symbol_name",
    [
        "OpenAEVDetectionHelper",
        "OpenAEVCollectorHelper",
        "OpenAEVInjectorHelper",
        "OpenAEVConfigHelper",
        "ListenQueue",
        "PingAlive",
    ],
)
def test_helper_symbol_retention_imports_without_error(symbol_name: str) -> None:
    """Verifies deprecated helper symbols remain importable from pyoaev.helpers."""
    symbol, import_error = _when_importing_helper_symbol(symbol_name)
    _then_import_succeeds(import_error, symbol_name)
    _then_symbol_exists(symbol, symbol_name)


@pytest.mark.parametrize(
    ("dependency_name", "pattern"),
    [
        ("pika", r"^\s*(?:import\s+pika\b|from\s+pika\b)"),
        ("thefuzz", r"^\s*(?:import\s+thefuzz\b|from\s+thefuzz\b)"),
    ],
)
def test_sdk_source_has_no_forbidden_external_runtime_imports(
    dependency_name: str, pattern: str
) -> None:
    """Verifies SDK source tree contains no direct runtime imports of forbidden deps."""
    files = _given_sdk_source_files()
    matches = _when_searching_for_pattern(files, pattern)
    _then_no_matches_found(matches)


def test_sdk_source_has_no_runtime_imports_from_pyoaev() -> None:
    """Verifies SDK source tree contains no import/from statements for pyoaev."""
    files = _given_sdk_source_files()
    matches = _when_searching_for_pattern(files, r"^\s*(?:from|import)\s+pyoaev(?:\.|\b)")
    _then_no_matches_found(matches)


@pytest.mark.parametrize(
    ("artifact_name", "pattern"),
    [
        ("ListenQueue", r"^\s*class\s+ListenQueue\b"),
        ("PingAlive", r"^\s*class\s+PingAlive\b"),
        ("OpenAEVConfigHelper", r"^\s*class\s+OpenAEVConfigHelper\b"),
        ("OpenAEVCollectorHelper", r"^\s*class\s+OpenAEVCollectorHelper\b"),
        ("OpenAEVInjectorHelper", r"^\s*class\s+OpenAEVInjectorHelper\b"),
        ("OpenAEVDetectionHelper", r"^\s*class\s+OpenAEVDetectionHelper\b"),
        ("create_mq_ssl_context", r"^\s*def\s+create_mq_ssl_context\b"),
    ],
)
def test_sdk_source_does_not_define_legacy_helper_artifacts(
    artifact_name: str, pattern: str
) -> None:
    """Verifies legacy helper artifacts are absent from SDK source files."""
    files = _given_sdk_source_files()
    matches = _when_searching_for_pattern(files, pattern)
    _then_no_matches_found(matches)


def test_dependency_direction_sdk_tree_has_no_runtime_imports_from_pyoaev() -> None:
    """Verifies dependency direction by scanning all Python files under libs/xtm-oaev-sdk."""
    files = _given_sdk_source_files()
    matches = _when_searching_for_pattern(files, r"^\s*(?:from|import)\s+pyoaev(?:\.|\b)")
    _then_no_matches_found(matches)


def test_blind_1_base_py_has_no_unused_openaev_annotation_import() -> None:
    """Verifies pyoaev.base no longer keeps unused `from .client import OpenAEV` import."""
    base_path = _PYOAEV_ROOT / "base.py"
    matches = _when_searching_in_file(base_path, r"^\s*from\s+\.client\s+import\s+OpenAEV\b")
    _then_no_matches_found(matches)


def test_blind_1_mixins_py_has_no_unused_pyoaev_annotation_import() -> None:
    """Verifies pyoaev.mixins no longer keeps unused `import pyoaev` for annotations."""
    mixins_path = _PYOAEV_ROOT / "mixins.py"
    matches = _when_searching_in_file(mixins_path, r"^\s*import\s+pyoaev\b")
    _then_no_matches_found(matches)
