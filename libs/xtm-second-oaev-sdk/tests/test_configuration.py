"""Tests for configuration public surface."""

from pathlib import Path
from typing import Any

import pytest
import xtm_second_oaev_sdk as sdk
from pydantic import ValidationError


def _given_public_module() -> Any:
    return sdk


def _given_required_symbol(module: Any, symbol_name: str) -> Any:
    assert hasattr(module, symbol_name), f"Missing public symbol: {symbol_name}"
    return getattr(module, symbol_name)


def _given_missing_config_file_path(tmp_path: Path) -> str:
    return str(tmp_path / "missing-config.yml")


def _given_configuration(
    module: Any,
    config_hints: dict[str, dict[str, Any] | str],
    config_values: dict[str, Any] | None,
    config_file_path: str,
) -> Any:
    configuration = _given_required_symbol(module, "Configuration")
    return configuration(
        config_hints=config_hints,
        config_values=config_values,
        config_file_path=config_file_path,
    )


def _given_config_hints_for_priority() -> dict[str, dict[str, Any]]:
    return {
        "target": {
            "env": "XTM_OAEV_TARGET",
            "file_path": ["section", "target"],
            "default": "default-value",
        }
    }


def _given_config_values_for_priority() -> dict[str, dict[str, str]]:
    return {"section": {"target": "file-value"}}


def _given_set_env(monkeypatch: pytest.MonkeyPatch, key: str, value: str | None) -> None:
    if value is None:
        monkeypatch.delenv(key, raising=False)
    else:
        monkeypatch.setenv(key, value)


def _when_set_configuration_value(configuration: Any, key: str, value: Any) -> None:
    configuration.set(key, value)


def _when_get_configuration_value(configuration: Any, key: str) -> Any:
    return configuration.get(key)


def _when_get_environment_value(environment_source: Any, env_key: str | None) -> Any:
    return environment_source.get(env_key)


def _when_get_dictionary_value(dictionary_source: Any, path: list[str] | None, source_dict: dict[str, Any]) -> Any:
    return dictionary_source.get(path, source_dict)


def _when_assign_attribute(target: Any, attribute: str, value: Any) -> None:
    setattr(target, attribute, value)


def _when_create_base_model_with_extra(base_config_model: Any) -> Any:
    class _Model(base_config_model):
        required: str

    return _Model(required="ok", extra_value="extra")


def _when_create_base_model_for_frozen_check(base_config_model: Any) -> Any:
    class _Model(base_config_model):
        value: int

    return _Model(value=1)


def _when_spy_on_model_copy(
    monkeypatch: pytest.MonkeyPatch,
    configuration_hint: Any,
) -> dict[str, Any]:
    original = configuration_hint.model_copy
    recorder: dict[str, Any] = {"called": False, "update": None}

    def _spy(self: Any, *args: Any, **kwargs: Any) -> Any:
        recorder["called"] = True
        recorder["update"] = kwargs.get("update")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(configuration_hint, "model_copy", _spy, raising=True)
    return recorder


def _when_get_private_hint(configuration: Any, key: str) -> Any:
    return configuration._Configuration__config_hints[key]  # noqa: SLF001


def _then_value_equals(actual: Any, expected: Any) -> None:
    assert actual == expected


def _then_value_is_none(actual: Any) -> None:
    assert actual is None


def _then_public_symbols_exist(module: Any, symbols: list[str]) -> None:
    for symbol in symbols:
        assert hasattr(module, symbol), f"Missing public symbol: {symbol}"


def _then_protocol_runtime_checkable(protocol: Any) -> None:
    assert getattr(protocol, "_is_runtime_protocol", False) is True


def _then_instance_satisfies_protocol(instance: Any, protocol: Any) -> None:
    assert isinstance(instance, protocol)


def _then_raises_validation_error(callable_obj: Any, *args: Any, **kwargs: Any) -> None:
    with pytest.raises(ValidationError):
        callable_obj(*args, **kwargs)


def _then_raises_assertion_error(callable_obj: Any, *args: Any, **kwargs: Any) -> None:
    with pytest.raises(AssertionError):
        callable_obj(*args, **kwargs)


def _then_hint_fields_match(hint: Any, expected: dict[str, Any]) -> None:
    assert hint.data == expected["data"]
    assert hint.env == expected["env"]
    assert hint.file_path == expected["file_path"]
    assert hint.is_number == expected["is_number"]
    assert hint.default == expected["default"]


def _then_hint_is_instance_of(hint: Any, hint_class: Any) -> None:
    assert isinstance(hint, hint_class)


def _then_model_copy_update_used(spy: dict[str, Any], expected_update: dict[str, Any]) -> None:
    assert spy["called"] is True
    assert spy["update"] == expected_update


def _then_model_allows_extra_fields(model_instance: Any, key: str, expected: Any) -> None:
    assert model_instance.model_dump()[key] == expected


def _then_model_fields_include(model_class: Any, expected_fields: set[str]) -> None:
    assert expected_fields.issubset(set(model_class.model_fields.keys()))


def test_public_surface_exports_configuration_symbols() -> None:
    """It exposes all expected configuration-related public symbols."""
    module = _given_public_module()
    _then_public_symbols_exist(
        module,
        [
            "ConfigurationProtocol",
            "Configuration",
            "ConfigurationHint",
            "EnvironmentSource",
            "DictionarySource",
            "BaseConfigModel",
            "ConfigLoaderOAEV",
            "ConfigLoaderCollector",
            "CONFIGURATION_TYPES",
        ],
    )


def test_configuration_resolves_with_override_priority(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """It prioritizes override over env, file, and default."""
    module = _given_public_module()
    hints = _given_config_hints_for_priority()
    config_values = _given_config_values_for_priority()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, hints, config_values, missing_path)
    _given_set_env(monkeypatch, "XTM_OAEV_TARGET", "env-value")
    _when_set_configuration_value(configuration, "target", "override-value")
    result = _when_get_configuration_value(configuration, "target")
    _then_value_equals(result, "override-value")


def test_configuration_get_prefers_env_when_no_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """It reads environment value when no override is set."""
    module = _given_public_module()
    hints = _given_config_hints_for_priority()
    config_values = _given_config_values_for_priority()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, hints, config_values, missing_path)
    _given_set_env(monkeypatch, "XTM_OAEV_TARGET", "env-value")
    result = _when_get_configuration_value(configuration, "target")
    _then_value_equals(result, "env-value")


def test_configuration_get_prefers_file_when_env_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """It reads file-backed value when env is absent."""
    module = _given_public_module()
    hints = _given_config_hints_for_priority()
    config_values = _given_config_values_for_priority()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, hints, config_values, missing_path)
    _given_set_env(monkeypatch, "XTM_OAEV_TARGET", None)
    result = _when_get_configuration_value(configuration, "target")
    _then_value_equals(result, "file-value")


def test_configuration_get_falls_back_to_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """It uses default when override, env, and file are unavailable."""
    module = _given_public_module()
    hints = _given_config_hints_for_priority()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, hints, {}, missing_path)
    _given_set_env(monkeypatch, "XTM_OAEV_TARGET", None)
    result = _when_get_configuration_value(configuration, "target")
    _then_value_equals(result, "default-value")


def test_configuration_get_returns_none_for_unknown_key(tmp_path: Path) -> None:
    """It returns None for an unknown configuration key."""
    module = _given_public_module()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, {"known": {"default": "x"}}, {}, missing_path)
    result = _when_get_configuration_value(configuration, "unknown")
    _then_value_is_none(result)


def test_configuration_set_creates_new_hint_for_new_key(tmp_path: Path) -> None:
    """It creates a new ConfigurationHint when setting a new key."""
    module = _given_public_module()
    hint_class = _given_required_symbol(module, "ConfigurationHint")
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, {}, {}, missing_path)
    _when_set_configuration_value(configuration, "new_key", "new-value")
    hint = _when_get_private_hint(configuration, "new_key")
    _then_hint_is_instance_of(hint, hint_class)
    _then_value_equals(hint.data, "new-value")


def test_configuration_set_updates_existing_hint_with_model_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It updates existing hints via model_copy(update={'data': value})."""
    module = _given_public_module()
    hint_class = _given_required_symbol(module, "ConfigurationHint")
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, {"target": {"default": "old"}}, {}, missing_path)
    spy = _when_spy_on_model_copy(monkeypatch, hint_class)
    _when_set_configuration_value(configuration, "target", "new")
    _then_model_copy_update_used(spy, {"data": "new"})


def test_configuration_coerces_number_when_is_number_true(tmp_path: Path) -> None:
    """It coerces values to int when is_number hint is true."""
    module = _given_public_module()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(
        module,
        {"count": {"default": "7", "is_number": True}},
        {},
        missing_path,
    )
    result = _when_get_configuration_value(configuration, "count")
    _then_value_equals(result, 7)


def test_configuration_coerces_truthy_strings_to_true(tmp_path: Path) -> None:
    """It coerces yes/true strings to True case-insensitively."""
    module = _given_public_module()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(
        module,
        {"enabled": {"default": "YeS"}},
        {},
        missing_path,
    )
    result = _when_get_configuration_value(configuration, "enabled")
    _then_value_equals(result, True)


def test_configuration_coerces_falsy_strings_to_false(tmp_path: Path) -> None:
    """It coerces no/false strings to False case-insensitively."""
    module = _given_public_module()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(
        module,
        {"enabled": {"default": "FaLsE"}},
        {},
        missing_path,
    )
    result = _when_get_configuration_value(configuration, "enabled")
    _then_value_equals(result, False)


def test_configuration_coerces_empty_string_to_none(tmp_path: Path) -> None:
    """It coerces empty strings to None."""
    module = _given_public_module()
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(
        module,
        {"value": {"default": ""}},
        {},
        missing_path,
    )
    result = _when_get_configuration_value(configuration, "value")
    _then_value_is_none(result)


def test_configuration_hint_is_frozen() -> None:
    """It prevents assignment on ConfigurationHint instances."""
    module = _given_public_module()
    configuration_hint = _given_required_symbol(module, "ConfigurationHint")
    hint = configuration_hint(data="a")
    _then_raises_validation_error(_when_assign_attribute, hint, "data", "b")


def test_configuration_hint_stores_all_fields() -> None:
    """It stores data, env, file_path, is_number, and default fields."""
    module = _given_public_module()
    configuration_hint = _given_required_symbol(module, "ConfigurationHint")
    hint = configuration_hint(
        data="x",
        env="XTM_OAEV_ENV",
        file_path=["section", "key"],
        is_number=True,
        default="fallback",
    )
    _then_hint_fields_match(
        hint,
        {
            "data": "x",
            "env": "XTM_OAEV_ENV",
            "file_path": ["section", "key"],
            "is_number": True,
            "default": "fallback",
        },
    )


def test_configuration_protocol_is_runtime_checkable_and_implemented(tmp_path: Path) -> None:
    """It is runtime-checkable and Configuration satisfies it."""
    module = _given_public_module()
    protocol = _given_required_symbol(module, "ConfigurationProtocol")
    missing_path = _given_missing_config_file_path(tmp_path)
    configuration = _given_configuration(module, {}, {}, missing_path)
    _then_protocol_runtime_checkable(protocol)
    _then_instance_satisfies_protocol(configuration, protocol)


def test_environment_source_get_returns_none_for_none_key() -> None:
    """It returns None when env var key is None."""
    module = _given_public_module()
    environment_source = _given_required_symbol(module, "EnvironmentSource")
    result = _when_get_environment_value(environment_source, None)
    _then_value_is_none(result)


def test_environment_source_get_returns_none_for_empty_key() -> None:
    """It returns None when env var key is empty."""
    module = _given_public_module()
    environment_source = _given_required_symbol(module, "EnvironmentSource")
    result = _when_get_environment_value(environment_source, "")
    _then_value_is_none(result)


def test_environment_source_get_returns_existing_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """It returns environment value when variable exists."""
    module = _given_public_module()
    environment_source = _given_required_symbol(module, "EnvironmentSource")
    _given_set_env(monkeypatch, "EXISTING_VAR", "value-from-env")
    result = _when_get_environment_value(environment_source, "EXISTING_VAR")
    _then_value_equals(result, "value-from-env")


def test_environment_source_get_returns_none_for_missing_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """It returns None when environment variable does not exist."""
    module = _given_public_module()
    environment_source = _given_required_symbol(module, "EnvironmentSource")
    _given_set_env(monkeypatch, "NONEXISTENT_VAR", None)
    result = _when_get_environment_value(environment_source, "NONEXISTENT_VAR")
    _then_value_is_none(result)


def test_dictionary_source_get_returns_none_for_none_path() -> None:
    """It returns None when dictionary path is None."""
    module = _given_public_module()
    dictionary_source = _given_required_symbol(module, "DictionarySource")
    result = _when_get_dictionary_value(dictionary_source, None, {"section": {"key": "value"}})
    _then_value_is_none(result)


def test_dictionary_source_get_returns_nested_value() -> None:
    """It returns value for a valid two-level path."""
    module = _given_public_module()
    dictionary_source = _given_required_symbol(module, "DictionarySource")
    result = _when_get_dictionary_value(
        dictionary_source,
        ["section", "key"],
        {"section": {"key": "val"}},
    )
    _then_value_equals(result, "val")


def test_dictionary_source_get_returns_none_for_missing_nested_key() -> None:
    """It returns None when nested key is missing."""
    module = _given_public_module()
    dictionary_source = _given_required_symbol(module, "DictionarySource")
    result = _when_get_dictionary_value(
        dictionary_source,
        ["section", "missing"],
        {"section": {"key": "val"}},
    )
    _then_value_is_none(result)


def test_dictionary_source_get_raises_for_invalid_path_length() -> None:
    """It raises AssertionError when path is not exactly two elements."""
    module = _given_public_module()
    dictionary_source = _given_required_symbol(module, "DictionarySource")
    _then_raises_assertion_error(
        _when_get_dictionary_value,
        dictionary_source,
        ["section"],
        {"section": {"key": "val"}},
    )


def test_base_config_model_is_frozen() -> None:
    """It prevents assignment on BaseConfigModel subclasses."""
    module = _given_public_module()
    base_config_model = _given_required_symbol(module, "BaseConfigModel")
    instance = _when_create_base_model_for_frozen_check(base_config_model)
    _then_raises_validation_error(_when_assign_attribute, instance, "value", 2)


def test_base_config_model_allows_extra_fields() -> None:
    """It accepts extra fields on BaseConfigModel subclasses."""
    module = _given_public_module()
    base_config_model = _given_required_symbol(module, "BaseConfigModel")
    instance = _when_create_base_model_with_extra(base_config_model)
    _then_model_allows_extra_fields(instance, "extra_value", "extra")


def test_config_loader_oaev_has_expected_fields() -> None:
    """It defines url, token, and tenant_id fields."""
    module = _given_public_module()
    config_loader_oaev = _given_required_symbol(module, "ConfigLoaderOAEV")
    _then_model_fields_include(config_loader_oaev, {"url", "token", "tenant_id"})


def test_config_loader_collector_has_expected_fields() -> None:
    """It defines id, name, log_level, period, and icon_filepath fields."""
    module = _given_public_module()
    config_loader_collector = _given_required_symbol(module, "ConfigLoaderCollector")
    _then_model_fields_include(
        config_loader_collector,
        {"id", "name", "log_level", "period", "icon_filepath"},
    )
