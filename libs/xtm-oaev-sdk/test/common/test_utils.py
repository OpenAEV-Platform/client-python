"""Tests for xtm_oaev_sdk utils public surface."""

import dataclasses
import logging
import subprocess
import sys
import warnings
from typing import Any

import pytest
import xtm_oaev_sdk as sdk


@dataclasses.dataclass
class _SampleDataClass:
    name: str
    value: int


class _UnsupportedType:
    pass


class _RecordingLogger:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def debug(self, message: str, **kwargs: Any) -> None:
        self.calls.append({"level": "debug", "message": message, "kwargs": kwargs})

    def info(self, message: str, **kwargs: Any) -> None:
        self.calls.append({"level": "info", "message": message, "kwargs": kwargs})

    def warning(self, message: str, **kwargs: Any) -> None:
        self.calls.append({"level": "warning", "message": message, "kwargs": kwargs})

    def error(self, message: str, **kwargs: Any) -> None:
        self.calls.append({"level": "error", "message": message, "kwargs": kwargs})


def _given_public_symbol(name: str) -> Any:
    return getattr(sdk, name)


def _given_app_logger() -> Any:
    app_logger_cls = _given_public_symbol("AppLogger")
    return app_logger_cls(logging.INFO, json_logging=False, name="initial")


def _given_app_logger_with_recording_logger() -> tuple[Any, _RecordingLogger]:
    app_logger = _given_app_logger()
    recorder = _RecordingLogger()
    app_logger.local_logger = recorder
    return app_logger, recorder


def _given_json_encoder() -> Any:
    encoder_cls = _given_public_symbol("EnhancedJSONEncoder")
    return encoder_cls()


def _given_clean_root_logging_state() -> logging.Logger:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.NOTSET)
    return root_logger


def _when_call_logger_with_name(app_logger: Any, name: str) -> Any:
    return app_logger(name)


def _when_call_app_logger_method(
    app_logger: Any, method_name: str, message: str, meta: dict[str, Any]
) -> None:
    getattr(app_logger, method_name)(message, meta)


def _when_set_third_party_logger_level(lib: str, level: int) -> None:
    app_logger_cls = _given_public_symbol("AppLogger")
    app_logger_cls.setup_logger_level(lib, level)


def _when_encode_with_default(encoder: Any, value: Any) -> Any:
    return encoder.default(value)


def _when_encode_unsupported_type_raises(encoder: Any, value: Any) -> Exception:
    with pytest.raises(TypeError) as exc_info:
        encoder.default(value)
    return exc_info.value


def _when_copy_dict(src: dict[str, Any], dest: dict[str, Any]) -> None:
    copy_dict_fn = _given_public_symbol("copy_dict")
    copy_dict_fn(src=src, dest=dest)


def _when_remove_none_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    remove_none_fn = _given_public_symbol("remove_none_from_dict")
    return remove_none_fn(data)


def _when_call_logger(level: int, json_logging: bool) -> Any:
    logger_fn = _given_public_symbol("logger")
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        return logger_fn(level, json_logging)


def _when_setup_logging(level: int, json_logging: bool) -> None:
    setup_fn = _given_public_symbol("setup_logging_config")
    setup_fn(level, json_logging=json_logging)


def _then_logger_name_switched_and_self_returned(
    original: Any, switched: Any, expected_name: str
) -> None:
    assert switched is original
    assert original.local_logger.name == expected_name


def _then_recording_logger_has_call(
    recorder: _RecordingLogger,
    expected_level: str,
    expected_message: str,
    expected_meta: dict[str, Any],
) -> None:
    assert len(recorder.calls) == 1
    call = recorder.calls[0]
    assert call["level"] == expected_level
    assert call["message"] == expected_message
    assert call["kwargs"]["extra"] == {"attributes": expected_meta}
    if expected_level == "error":
        assert call["kwargs"]["exc_info"] == 1


def _then_third_party_logger_level_is(lib: str, expected_level: int) -> None:
    assert logging.getLogger(lib).level == expected_level


def _then_runtime_checkable_protocol_satisfied(instance: Any) -> None:
    protocol_cls = _given_public_symbol("AppLoggerProtocol")
    assert isinstance(instance, protocol_cls)


def _then_encoded_object_equals(encoded: Any, expected: Any) -> None:
    assert encoded == expected


def _then_type_error_for_unsupported_type(exc: Exception) -> None:
    assert "not json serializable" in str(exc).lower()


def _then_dict_equals(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert actual == expected


def _then_is_app_logger_instance(instance: Any) -> None:
    app_logger_cls = _given_public_symbol("AppLogger")
    assert isinstance(instance, app_logger_cls)


def _then_root_logger_has_json_formatter(expected_level: int) -> None:
    custom_formatter_cls = _given_public_symbol("CustomJsonFormatter")
    root_logger = logging.getLogger()
    assert root_logger.handlers
    assert isinstance(root_logger.handlers[0].formatter, custom_formatter_cls)
    assert root_logger.level == expected_level


def _then_root_logger_uses_basic_config_level(expected_level: int) -> None:
    root_logger = logging.getLogger()
    assert root_logger.level == expected_level


def test_app_logger_call_switches_name_and_returns_self() -> None:
    """Verify AppLogger.__call__ switches logger name and returns self."""
    app_logger = _given_app_logger()
    switched = _when_call_logger_with_name(app_logger, "switched")
    _then_logger_name_switched_and_self_returned(app_logger, switched, "switched")


@pytest.mark.parametrize("level_name", ["debug", "info", "warning", "error"])
def test_app_logger_logs_with_meta_dict(level_name: str) -> None:
    """Verify AppLogger log methods accept metadata and call the right level."""
    app_logger, recorder = _given_app_logger_with_recording_logger()
    _when_call_app_logger_method(app_logger, level_name, "message", {"k": "v"})
    _then_recording_logger_has_call(recorder, level_name, "message", {"k": "v"})


def test_app_logger_setup_logger_level_adjusts_third_party_logger() -> None:
    """Verify AppLogger.setup_logger_level updates external logger level."""
    _when_set_third_party_logger_level("third.party.lib", logging.ERROR)
    _then_third_party_logger_level_is("third.party.lib", logging.ERROR)


def test_app_logger_protocol_runtime_checkable() -> None:
    """Verify AppLogger satisfies AppLoggerProtocol runtime isinstance check."""
    app_logger = _given_app_logger()
    _then_runtime_checkable_protocol_satisfied(app_logger)


def test_enhanced_json_encoder_serializes_dataclass() -> None:
    """Verify EnhancedJSONEncoder serializes dataclass instances via asdict."""
    encoder = _given_json_encoder()
    encoded = _when_encode_with_default(encoder, _SampleDataClass(name="n", value=1))
    _then_encoded_object_equals(encoded, {"name": "n", "value": 1})


def test_enhanced_json_encoder_raises_type_error_for_unsupported_types() -> None:
    """Verify EnhancedJSONEncoder raises TypeError on unsupported objects."""
    encoder = _given_json_encoder()
    exc = _when_encode_unsupported_type_raises(encoder, _UnsupportedType())
    _then_type_error_for_unsupported_type(exc)


def test_copy_dict_flattens_nested_dict_keys() -> None:
    """Verify copy_dict flattens nested dict keys to bracket notation."""
    destination: dict[str, Any] = {}
    _when_copy_dict(src={"filters": {"type": "malware"}}, dest=destination)
    _then_dict_equals(destination, {"filters[type]": "malware"})


def test_copy_dict_copies_non_dict_values_directly() -> None:
    """Verify copy_dict copies non-dict values without transformation."""
    destination: dict[str, Any] = {}
    _when_copy_dict(src={"name": "sdk", "count": 2}, dest=destination)
    _then_dict_equals(destination, {"name": "sdk", "count": 2})


def test_remove_none_from_dict_strips_none_valued_keys() -> None:
    """Verify remove_none_from_dict removes entries with None values."""
    result = _when_remove_none_from_dict({"a": 1, "b": None, "c": "x"})
    _then_dict_equals(result, {"a": 1, "c": "x"})


def test_remove_none_from_dict_keeps_non_none_values() -> None:
    """Verify remove_none_from_dict keeps entries with non-None values."""
    result = _when_remove_none_from_dict({"a": 0, "b": False, "c": ""})
    _then_dict_equals(result, {"a": 0, "b": False, "c": ""})


def test_logger_function_returns_app_logger() -> None:
    """Verify logger() returns an AppLogger without warning."""
    logger_instance = _when_call_logger(logging.INFO, json_logging=False)
    _then_is_app_logger_instance(logger_instance)


def test_setup_logging_config_json_logging_true_sets_json_handler() -> None:
    """Verify setup_logging_config configures JSON formatter when enabled."""
    _given_clean_root_logging_state()
    _when_setup_logging(logging.INFO, json_logging=True)
    _then_root_logger_has_json_formatter(logging.INFO)


def test_setup_logging_config_json_logging_false_uses_basic_config() -> None:
    """Verify setup_logging_config uses basicConfig when JSON logging is disabled."""
    _given_clean_root_logging_state()
    _when_setup_logging(logging.DEBUG, json_logging=False)
    _then_root_logger_uses_basic_config_level(logging.DEBUG)


def test_importing_utils_does_not_raise_jsonlogger_deprecation_warning() -> None:
    """Verify the JSON formatter uses the non-deprecated pythonjsonlogger path."""
    result = subprocess.run(
        [
            sys.executable,
            "-W",
            "error::DeprecationWarning",
            "-c",
            "import xtm_oaev_sdk",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
