"""Configuration management: hint-based value resolution.

Provides the Configuration class that resolves values from multiple
sources (environment, files, overrides) using a hint-based lookup system.

The Configuration class is the primary interface for SDK consumers to
access typed configuration values.

Example:
    >>> config = Configuration({
    ...     "log_level": {"env": "LOG_LEVEL", "default": "info"},
    ...     "api_url": {"env": "API_URL", "file_path": ["opencti", "url"]},
    ... })
    >>> config.get("log_level")
    'info'
    >>> config.set("log_level", "debug")
    >>> config.get("log_level")
    'debug'
"""

import os
import os.path
from typing import Any, Protocol, runtime_checkable

import yaml
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings

from xtm_oaev_sdk._core.configuration.connector_config_schema_generator import (
    ConnectorConfigSchemaGenerator,
)
from xtm_oaev_sdk._core.configuration.sources import DictionarySource, EnvironmentSource

__all__ = [
    "CONFIGURATION_TYPES",
    "Configuration",
    "ConfigurationHint",
    "ConfigurationProtocol",
]

CONFIGURATION_TYPES = str | int | bool | Any | None
"""Union type for configuration values."""


@runtime_checkable
class ConfigurationProtocol(Protocol):
    """Behavioral contract for configuration services.

    Any configuration implementation used by SDK consumers must satisfy
    this protocol. The built-in Configuration class implements it.

    Methods:
        get: Retrieve a typed configuration value by key.
        set: Override a configuration value at runtime.
        schema: Generate the connector configuration JSON schema.
    """

    def get(self, config_key: str) -> CONFIGURATION_TYPES:
        """Get configuration value by key."""
        ...

    def set(self, config_key: str, value: CONFIGURATION_TYPES) -> None:
        """Set a runtime override for a configuration key."""
        ...

    def schema(self) -> dict[str, Any]:
        """Generate the configuration JSON schema."""
        ...


def _is_truthy(value: str) -> bool:
    """Check if a string represents a truthy value.

    Args:
        value: String to test (case-insensitive).

    Returns:
        True if value is "yes" or "true".
    """
    return value.lower() in ["yes", "true"]


def _is_falsy(value: str) -> bool:
    """Check if a string represents a falsy value.

    Args:
        value: String to test (case-insensitive).

    Returns:
        True if value is "no" or "false".
    """
    return value.lower() in ["no", "false"]


class ConfigurationHint(BaseModel):
    """An individual configuration hint defining where a value can be found.

    Hints specify the resolution strategy for a configuration key:
    which environment variable to check, which file path to follow,
    and what default to use if no source provides a value.

    This model is frozen (immutable after creation). Use
    ``model_copy(update={...})`` to create modified instances.

    Args:
        data: Override value. When set, this value is returned directly.
        env: Environment variable name to read.
        file_path: JSON path (nested keys) in the config file.
        is_number: Whether to interpret the resolved value as an integer.
        default: Fallback value when no source provides one.

    Example:
        >>> hint = ConfigurationHint(env="LOG_LEVEL", default="info")
        >>> # To override: create a new instance
        >>> overridden = hint.model_copy(update={"data": "debug"})
    """

    model_config = ConfigDict(frozen=True)

    data: CONFIGURATION_TYPES = Field(default=None)
    env: str | None = Field(default=None)
    file_path: list[str] | None = Field(default=None)
    is_number: bool | None = Field(default=False)
    default: CONFIGURATION_TYPES = Field(default=None)


class Configuration:
    """Hint-based configuration resolver with multi-source lookup.

    Resolves configuration values by checking (in priority order):
    1. Explicit override via ``.set()``
    2. Environment variable (if ``env`` hint provided)
    3. Config file value (if ``file_path`` hint provided)
    4. Default value (if ``default`` hint provided)

    Args:
        config_hints: Mapping of config keys to hint definitions.
            Values can be dicts (parsed as ConfigurationHint) or strings
            (treated as default values).
        config_values: Pre-loaded configuration dict (e.g., from YAML).
        config_file_path: Path to YAML config file. Defaults to ./config.yml.
        config_base_model: Optional Pydantic BaseSettings for schema generation.

    Example:
        >>> config = Configuration({
        ...     "url": {"env": "API_URL", "default": "http://localhost"},
        ...     "timeout": {"env": "TIMEOUT", "is_number": True, "default": "30"},
        ... })
        >>> config.get("url")
        'http://localhost'
        >>> config.get("timeout")
        30
    """

    def __init__(
        self,
        config_hints: dict[str, dict[str, Any] | str],
        config_values: dict[str, Any] | None = None,
        config_file_path: str = os.path.join(os.curdir, "config.yml"),
        config_base_model: BaseSettings | None = None,
    ):
        self.__config_hints: dict[str, ConfigurationHint] = {
            key: (
                ConfigurationHint(**value)
                if isinstance(value, dict)
                else ConfigurationHint(default=value)
            )
            for key, value in config_hints.items()
        }

        file_contents = (
            yaml.load(open(config_file_path), Loader=yaml.FullLoader)
            if os.path.isfile(config_file_path)
            else {}
        )

        self.__config_values = (config_values or {}) | file_contents
        self.__base_model = config_base_model

    def get(self, config_key: str) -> CONFIGURATION_TYPES:
        """Get the resolved value for a configuration key.

        Resolution order: override → env var → file → default.

        Args:
            config_key: The configuration key to look up.

        Returns:
            The resolved value, or None if the key is unknown or
            no source provides a value.
        """
        config = self.__config_hints.get(config_key)
        if config is None:
            return None

        return self.__process_value_to_type(
            (
                self.__dig_config_sources_for_key(config)
                if config.data is None
                else config.data
            ),
            config.is_number,
        )

    def set(self, config_key: str, value: CONFIGURATION_TYPES) -> None:
        """Set a runtime override for a configuration key.

        After calling this, ``get(config_key)`` will return the
        overridden value regardless of environment or file sources.

        Args:
            config_key: The configuration key to override.
            value: The new value to return for this key.
        """
        if config_key not in self.__config_hints:
            self.__config_hints[config_key] = ConfigurationHint(data=value)
        else:
            self.__config_hints[config_key] = self.__config_hints[
                config_key
            ].model_copy(update={"data": value})

    def schema(self) -> dict[str, Any]:
        """Generate the connector configuration JSON schema.

        Uses the configured base model's Pydantic schema generation
        with the ConnectorConfigSchemaGenerator for flattened output.

        Returns:
            A JSON schema dict describing all configuration properties.

        Raises:
            AttributeError: If no config_base_model was provided.
        """
        return self.__base_model.model_json_schema(  # type: ignore[union-attr]
            by_alias=False,
            schema_generator=ConnectorConfigSchemaGenerator,
            mode="validation",
        )

    @staticmethod
    def __process_value_to_type(
        value: CONFIGURATION_TYPES, is_number_hint: bool | None
    ) -> CONFIGURATION_TYPES:
        if value is None:
            return value
        if isinstance(value, int) or is_number_hint:
            return int(value)
        if isinstance(value, str):
            if _is_truthy(value):
                return True
            if _is_falsy(value):
                return False
            if len(value) == 0:
                return None
        return value

    def __dig_config_sources_for_key(
        self, config: ConfigurationHint
    ) -> CONFIGURATION_TYPES:
        result = EnvironmentSource.get(config.env) or DictionarySource.get(
            config.file_path, self.__config_values
        )
        return result or config.default
