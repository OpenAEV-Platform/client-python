"""REST client helpers owned by pyoaev: RequiredOptional, EncodedId, on_http_error."""

import dataclasses
import subprocess
import sys
from typing import Any

import pytest
import xtm_oaev_sdk as sdk

from pyoaev.exceptions import on_http_error
from pyoaev.utils import EncodedId, RequiredOptional


def _given_required_optional(**kwargs: Any) -> RequiredOptional:
    return RequiredOptional(**kwargs)


def _given_exclusive_spec() -> RequiredOptional:
    return _given_required_optional(exclusive=("id", "key"))


def _given_function_raising(error: Exception):
    def function() -> None:
        raise error

    return function


def _when_set_required_optional_field_raises(
    instance: RequiredOptional, field_name: str, value: Any
) -> Exception:
    with pytest.raises(dataclasses.FrozenInstanceError) as exc_info:
        setattr(instance, field_name, value)
    return exc_info.value


def _when_validate_attrs(
    instance: RequiredOptional, data: dict[str, Any], excludes: list[str] | None = None
) -> None:
    instance.validate_attrs(data=data, excludes=excludes)


def _when_validate_attrs_raises(
    instance: RequiredOptional, data: dict[str, Any]
) -> Exception:
    with pytest.raises(AttributeError) as exc_info:
        _when_validate_attrs(instance, data)
    return exc_info.value


def _when_encode_id(value: Any) -> EncodedId:
    return EncodedId(value)


def _when_encode_invalid_id_raises(value: Any) -> Exception:
    with pytest.raises(TypeError) as exc_info:
        _when_encode_id(value)
    return exc_info.value


def _when_call_decorated_raises(function, error: type[Exception]) -> Exception:
    with pytest.raises(error) as exc_info:
        on_http_error(error)(function)()
    return exc_info.value


def _when_run(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", script],
        capture_output=True,
        text=True,
    )


def _then_contains_text(exc: Exception, text: str) -> None:
    assert text in str(exc)


def _then_error_is_frozen(exc: Exception) -> None:
    assert isinstance(exc, dataclasses.FrozenInstanceError)


def _then_encoded_object_equals(encoded: EncodedId, expected: str) -> None:
    assert isinstance(encoded, EncodedId)
    assert encoded == expected


def test_required_optional_is_frozen() -> None:
    """It rejects field assignment on RequiredOptional."""
    required_optional = _given_required_optional(required=("name",))
    exc = _when_set_required_optional_field_raises(
        required_optional, "required", ("id",)
    )
    _then_error_is_frozen(exc)


def test_required_optional_validate_attrs_missing_required_raises() -> None:
    """It raises when a required attribute is missing."""
    required_optional = _given_required_optional(required=("name", "type"))
    exc = _when_validate_attrs_raises(required_optional, {"name": "sdk"})
    _then_contains_text(exc, "Missing attributes")


@pytest.mark.parametrize(
    ("data", "expected_text"),
    [
        ({}, "Must provide one of these attributes"),
        ({"id": "1", "key": "2"}, "Provide only one of these attributes"),
    ],
)
def test_required_optional_validate_attrs_exclusive_violations_raise(
    data: dict[str, Any], expected_text: str
) -> None:
    """It raises when exclusive attributes are both missing or both present."""
    required_optional = _given_exclusive_spec()
    exc = _when_validate_attrs_raises(required_optional, data)
    _then_contains_text(exc, expected_text)


def test_required_optional_validate_attrs_excludes_skip_required_check() -> None:
    """It skips the required check for excluded attributes."""
    required_optional = _given_required_optional(required=("name", "type"))
    _when_validate_attrs(required_optional, {"name": "sdk"}, excludes=["type"])


def test_required_optional_validate_attrs_valid_data_passes() -> None:
    """It accepts data satisfying the required and exclusive rules."""
    required_optional = _given_required_optional(
        required=("name",), exclusive=("id", "key")
    )
    _when_validate_attrs(required_optional, {"name": "sdk", "id": "123"})


def test_encoded_id_url_encodes_strings() -> None:
    """It percent-encodes unsafe string characters."""
    encoded = _when_encode_id("hello world")
    _then_encoded_object_equals(encoded, "hello%20world")


def test_encoded_id_is_idempotent_when_reencoded() -> None:
    """It returns the same value when re-encoding an EncodedId."""
    encoded = _when_encode_id("hello world")
    _then_encoded_object_equals(_when_encode_id(encoded), "hello%20world")


def test_encoded_id_rejects_non_str_non_int_values() -> None:
    """It raises TypeError for unsupported value types."""
    exc = _when_encode_invalid_id_raises(3.14)
    _then_contains_text(exc, "Unsupported type received")


def test_encoded_id_accepts_int_and_returns_string_representation() -> None:
    """It passes integer values through as their string form."""
    encoded = _when_encode_id(42)
    _then_encoded_object_equals(encoded, "42")


def test_on_http_error_wraps_http_errors_into_the_given_type() -> None:
    """It re-raises an HTTP error as the given error, keeping its details."""
    http_error = sdk.OpenAEVHttpError("boom", 404, b"missing")
    exc = _when_call_decorated_raises(
        _given_function_raising(http_error), sdk.OpenAEVGetError
    )
    assert (exc.error_message, exc.response_code, exc.response_body) == (
        "boom",
        404,
        b"missing",
    )
    assert exc.__cause__ is http_error


def test_on_http_error_lets_other_errors_through() -> None:
    """It does not touch errors that are not HTTP errors."""
    exc = _when_call_decorated_raises(_given_function_raising(KeyError("k")), KeyError)
    _then_contains_text(exc, "k")


def test_on_http_error_returns_the_wrapped_result_and_metadata() -> None:
    """It returns the decorated function's result and keeps its name."""

    def answer() -> int:
        return 42

    decorated = on_http_error(sdk.OpenAEVGetError)(answer)
    assert decorated() == 42
    assert decorated.__name__ == "answer"


def test_rest_client_helpers_are_pyoaev_own_and_silent() -> None:
    """It serves the REST client helpers from pyoaev itself, without any warning."""
    result = _when_run(
        "import pyoaev.utils, pyoaev.exceptions, xtm_oaev_sdk as sdk\n"
        "assert pyoaev.utils.EncodedId.__module__ == 'pyoaev.utils'\n"
        "assert pyoaev.utils.RequiredOptional.__module__ == 'pyoaev.utils'\n"
        "assert pyoaev.exceptions.on_http_error.__module__ == 'pyoaev.exceptions'\n"
        "assert not hasattr(sdk, 'EncodedId')\n"
        "assert not hasattr(sdk, 'RequiredOptional')\n"
        "assert not hasattr(sdk, 'on_http_error')\n"
    )
    assert result.returncode == 0, result.stderr
