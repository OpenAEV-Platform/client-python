"""Tests for Phase C — SSL helpers extraction to SDK."""

import ast
import os
import pathlib
import re
import warnings
from typing import Any
from unittest.mock import MagicMock

import pytest


_PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
_HELPERS_PATH = _PROJECT_ROOT / "pyoaev" / "helpers.py"


def _given_sdk_module() -> Any:
    import xtm_second_oaev_sdk

    return xtm_second_oaev_sdk


def _given_sdk_ssl_functions() -> tuple[Any, Any, Any, Any]:
    from xtm_second_oaev_sdk import (
        data_to_temp_file,
        is_memory_certificate,
        ssl_cert_chain,
        ssl_verify_locations,
    )

    return data_to_temp_file, is_memory_certificate, ssl_cert_chain, ssl_verify_locations


def _given_private_is_base64_encoded() -> Any:
    from pyoaev.helpers import _is_base64_encoded

    return _is_base64_encoded


def _given_legacy_ssl_functions() -> tuple[Any, Any, Any, Any]:
    from pyoaev.helpers import (
        data_to_temp_file,
        is_memory_certificate,
        ssl_cert_chain,
        ssl_verify_locations,
    )

    return data_to_temp_file, is_memory_certificate, ssl_cert_chain, ssl_verify_locations


def _given_legacy_detection_helper() -> Any:
    from pyoaev.helpers import OpenAEVDetectionHelper

    return OpenAEVDetectionHelper(logger=MagicMock(), relevant_signatures_types=[])


def _given_helpers_source() -> str:
    return _HELPERS_PATH.read_text(encoding="utf-8")


def _given_helpers_ast(source: str) -> ast.Module:
    return ast.parse(source)


def _given_function_source(module_ast: ast.Module, source: str, function_name: str) -> str | None:
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node)
    return None


def _when_calling_data_to_temp_file(func: Any, content: str) -> str:
    return func(content)


def _when_calling_ssl_cert_chain(
    func: Any, context: MagicMock, cert_data: str, key_data: str, passphrase: str
) -> None:
    func(context, cert_data, key_data, passphrase)


def _when_calling_ssl_verify_locations(func: Any, context: MagicMock, certdata: str) -> None:
    func(context, certdata)


def _when_importing_from_helpers(symbol: str) -> list[warnings.WarningMessage]:
    namespace: dict[str, Any] = {}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        exec(f"from pyoaev.helpers import {symbol} as _imported_symbol", namespace)  # noqa: S102
    return caught


def _when_importing_from_sdk() -> list[warnings.WarningMessage]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        _given_sdk_ssl_functions()
    return caught


def _then_file_contains(path: str, expected: str) -> None:
    with open(path, encoding="utf-8") as file_handle:
        assert file_handle.read() == expected
    os.unlink(path)


def _then_contains_deprecation_warning(caught: list[warnings.WarningMessage]) -> None:
    assert any(isinstance(item.message, DeprecationWarning) for item in caught)


def _then_contains_no_deprecation_warning(caught: list[warnings.WarningMessage]) -> None:
    assert not any(isinstance(item.message, DeprecationWarning) for item in caught)


def test_sdk_exports_ssl_helpers_without_warning() -> None:
    """It imports SSL helpers from xtm_second_oaev_sdk without warnings."""
    caught = _when_importing_from_sdk()
    _then_contains_no_deprecation_warning(caught)


def test_sdk_all_includes_ssl_helpers() -> None:
    """It exposes all SSL helpers through xtm_second_oaev_sdk.__all__."""
    sdk = _given_sdk_module()
    for symbol in [
        "data_to_temp_file",
        "is_memory_certificate",
        "ssl_cert_chain",
        "ssl_verify_locations",
    ]:
        assert symbol in sdk.__all__


def test_helpers_legacy_ssl_function_bodies_are_removed() -> None:
    """It removes legacy SSL helper implementations from pyoaev.helpers."""
    source = _given_helpers_source()
    module_ast = _given_helpers_ast(source)
    legacy_markers = {
        "data_to_temp_file": ["tempfile.mkstemp", "os.fdopen", "open_file.write"],
        "is_memory_certificate": ['startswith("-----BEGIN")'],
        "ssl_cert_chain": ["load_cert_chain(cert, key, passphrase)", "os.unlink(cert_file_path)"],
        "ssl_verify_locations": ["load_verify_locations(cadata=certdata)", "load_verify_locations(cafile=certdata)"],
    }
    for function_name, markers in legacy_markers.items():
        function_source = _given_function_source(module_ast, source, function_name)
        if function_source is None:
            continue
        for marker in markers:
            assert marker not in function_source


def test_private_is_base64_encoded_stays_in_helpers() -> None:
    """_is_base64_encoded remains in pyoaev.helpers (not extracted to SDK)."""
    source = _given_helpers_source()
    assert "def _is_base64_encoded" in source
    assert "_is_base64_encoded" not in _given_sdk_module().__all__


@pytest.mark.parametrize(
    "symbol",
    ["data_to_temp_file", "is_memory_certificate", "ssl_cert_chain", "ssl_verify_locations"],
)
def test_deprecated_shims_warn_when_imported_from_helpers(symbol: str) -> None:
    """It raises DeprecationWarning when SSL helpers are imported from pyoaev.helpers."""
    caught = _when_importing_from_helpers(symbol)
    _then_contains_deprecation_warning(caught)


def test_importing_ssl_helpers_from_sdk_does_not_warn() -> None:
    """It does not raise DeprecationWarning on direct SDK imports."""
    caught = _when_importing_from_sdk()
    _then_contains_no_deprecation_warning(caught)


def test_data_to_temp_file_parity_between_sdk_and_legacy() -> None:
    """It keeps data_to_temp_file behavior parity."""
    sdk_data_to_temp_file, *_ = _given_sdk_ssl_functions()
    legacy_data_to_temp_file, *_ = _given_legacy_ssl_functions()
    sdk_path = _when_calling_data_to_temp_file(sdk_data_to_temp_file, "test content")
    legacy_path = _when_calling_data_to_temp_file(legacy_data_to_temp_file, "test content")
    _then_file_contains(sdk_path, "test content")
    _then_file_contains(legacy_path, "test content")


@pytest.mark.parametrize(
    ("certificate", "expected"),
    [("-----BEGIN CERTIFICATE-----", True), ("/path/to/cert.pem", False)],
)
def test_is_memory_certificate_parity_between_sdk_and_legacy(certificate: str, expected: bool) -> None:
    """It keeps is_memory_certificate behavior parity."""
    _, sdk_is_memory_certificate, _, _ = _given_sdk_ssl_functions()
    _, legacy_is_memory_certificate, _, _ = _given_legacy_ssl_functions()
    assert sdk_is_memory_certificate(certificate) == expected
    assert legacy_is_memory_certificate(certificate) == expected


def test_ssl_cert_chain_call_pattern_parity_between_sdk_and_legacy() -> None:
    """It keeps ssl_cert_chain call pattern parity."""
    _, _, sdk_ssl_cert_chain, _ = _given_sdk_ssl_functions()
    _, _, legacy_ssl_cert_chain, _ = _given_legacy_ssl_functions()
    sdk_context = MagicMock()
    legacy_context = MagicMock()
    _when_calling_ssl_cert_chain(sdk_ssl_cert_chain, sdk_context, "/tmp/cert.pem", "/tmp/key.pem", "secret")
    _when_calling_ssl_cert_chain(
        legacy_ssl_cert_chain, legacy_context, "/tmp/cert.pem", "/tmp/key.pem", "secret"
    )
    assert sdk_context.load_cert_chain.call_args == legacy_context.load_cert_chain.call_args


@pytest.mark.parametrize(
    "certdata",
    ["/tmp/ca.pem", "-----BEGIN CERTIFICATE-----inline"],
)
def test_ssl_verify_locations_call_pattern_parity_between_sdk_and_legacy(certdata: str) -> None:
    """It keeps ssl_verify_locations call pattern parity."""
    _, _, _, sdk_ssl_verify_locations = _given_sdk_ssl_functions()
    _, _, _, legacy_ssl_verify_locations = _given_legacy_ssl_functions()
    sdk_context = MagicMock()
    legacy_context = MagicMock()
    _when_calling_ssl_verify_locations(sdk_ssl_verify_locations, sdk_context, certdata)
    _when_calling_ssl_verify_locations(legacy_ssl_verify_locations, legacy_context, certdata)
    assert sdk_context.load_verify_locations.call_args == legacy_context.load_verify_locations.call_args


@pytest.mark.parametrize(
    ("value", "expected"),
    [("dGVzdA==", True), ("not base64!", False)],
)
def test_private_is_base64_encoded_behavior(value: str, expected: bool) -> None:
    """It keeps _is_base64_encoded behavior parity after extraction."""
    private_helper = _given_private_is_base64_encoded()
    assert private_helper(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("dGVzdA==", "test"), ("plain text", "plain text")],
)
def test_detection_helper_decode_value_keeps_behavior_after_private_move(
    value: str, expected: str
) -> None:
    """It keeps OpenAEVDetectionHelper._decode_value behavior unchanged."""
    helper = _given_legacy_detection_helper()
    assert helper._decode_value(value) == expected  # noqa: SLF001


def test_create_mq_ssl_context_imports_ssl_cert_chain_from_sdk() -> None:
    """It imports ssl_cert_chain from xtm_second_oaev_sdk for create_mq_ssl_context."""
    source = _given_helpers_source()
    assert re.search(r"from\s+xtm_oaev_sdk\s+import\s+.*ssl_cert_chain", source)
