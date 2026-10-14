"""Configuration resolution: override, then env var, then file, then default."""

import os.path
from typing import Any

import yaml
from pydantic_settings import BaseSettings
from xtm_oaev_sdk._core.configuration.sources import ConfigurationSources
from xtm_oaev_sdk._core.configuration.truthiness import Truthiness
from xtm_oaev_sdk.seam.configuration import (
    CONFIGURATION_TYPES,
    ConfigurationHint,
    ConfigurationSourcesPort,
    TruthinessPort,
)

__all__ = ["ConfigurationResolver"]


class ConfigurationResolver:
    """Implements ``ConfigurationResolverPort``."""

    def __init__(
        self,
        sources: ConfigurationSourcesPort | None = None,
        truthiness: TruthinessPort | None = None,
    ) -> None:
        self._sources = sources or ConfigurationSources()
        self._truthiness = truthiness or Truthiness()

    def build_hints(
        self, config_hints: dict[str, dict[str, Any] | str]
    ) -> dict[str, ConfigurationHint]:
        return {
            key: (
                ConfigurationHint(**value)
                if isinstance(value, dict)
                else ConfigurationHint(default=value)
            )
            for key, value in config_hints.items()
        }

    def load_values(
        self, config_values: dict[str, Any] | None, config_file_path: str
    ) -> dict[str, Any]:
        file_contents = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )
        return (config_values or {}) | file_contents

    def resolve(
        self, hint: ConfigurationHint, values: dict[str, Any]
    ) -> CONFIGURATION_TYPES:
        return self._process_value_to_type(
            (self._dig_sources(hint, values) if hint.data is None else hint.data),
            hint.is_number,
        )

    def override(
        self,
        hints: dict[str, ConfigurationHint],
        config_key: str,
        value: CONFIGURATION_TYPES,
    ) -> None:
        if config_key not in hints:
            hints[config_key] = ConfigurationHint(data=value)
        else:
            hints[config_key].data = value

    def generate_schema(
        self, base_model: BaseSettings | None, schema_generator: type
    ) -> dict[str, Any]:
        return base_model.model_json_schema(  # type: ignore[union-attr]
            by_alias=False,
            schema_generator=schema_generator,
            mode="validation",
        )

    def _process_value_to_type(
        self, value: CONFIGURATION_TYPES, is_number_hint: bool | None
    ) -> CONFIGURATION_TYPES:
        if value is None:
            return value
        if isinstance(value, int) or is_number_hint:
            return int(value)
        if isinstance(value, str):
            if self._truthiness.is_truthy(value):
                return True
            if self._truthiness.is_falsy(value):
                return False
            if len(value) == 0:
                return None
        return value

    def _dig_sources(
        self, hint: ConfigurationHint, values: dict[str, Any]
    ) -> CONFIGURATION_TYPES:
        result = self._sources.from_environment(
            hint.env
        ) or self._sources.from_dictionary(hint.file_path, values)
        return result or hint.default
