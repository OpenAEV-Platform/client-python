"""Configuration adapters: hint-based value resolution and settings loading.

Each adapter speaks the configuration seam contracts and delegates to the core
implementation of its port.

Example:
    >>> config = Configuration({
    ...     "log_level": {"env": "LOG_LEVEL", "default": "info"},
    ...     "api_url": {"env": "API_URL", "file_path": ["openaev", "url"]},
    ... })
    >>> config.get("log_level")
    'info'
    >>> config.set("log_level", "debug")
    >>> config.get("log_level")
    'debug'
"""

import os
from typing import Any, override

from pydantic.json_schema import GenerateJsonSchema
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from xtm_oaev_sdk._core.configuration import (
    ConfigurationResolver,
    ConfigurationSources,
    ConnectorSchemaTransformer,
    SettingsSourceSelector,
    Truthiness,
)
from xtm_oaev_sdk.seam.configuration import (
    CONFIGURATION_TYPES,
    BaseConfigModel,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    ConfigurationHint,
    ConfigurationProtocol,
    ConfigurationResolverPort,
    ConfigurationSourcesPort,
    ConnectorSchemaPort,
    HttpUrlToString,
    LogLevelToLower,
    SettingsSourcesPort,
    TimedeltaInSeconds,
    TruthinessPort,
)

__all__ = [
    "BaseConfigModel",
    "CONFIGURATION_TYPES",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "Configuration",
    "ConfigurationHint",
    "ConfigurationProtocol",
    "ConnectorConfigSchemaGenerator",
    "DictionarySource",
    "EnvironmentSource",
    "HttpUrlToString",
    "LogLevelToLower",
    "SettingsLoader",
    "TimedeltaInSeconds",
    "is_falsy",
    "is_truthy",
]

_truthiness: TruthinessPort = Truthiness()
_sources: ConfigurationSourcesPort = ConfigurationSources()
_resolver: ConfigurationResolverPort = ConfigurationResolver(_sources, _truthiness)
_schema: ConnectorSchemaPort = ConnectorSchemaTransformer()
_settings_sources: SettingsSourcesPort = SettingsSourceSelector()


def is_truthy(value: str) -> bool:
    """Asserts whether a given string signals a "True" value.

    :param value: value to test
    :type value: str

    :return: whether the string represents True or not.
    :rtype: bool
    """
    return _truthiness.is_truthy(value)


def is_falsy(value: str) -> bool:
    """Asserts whether a given string signals a "False" value.

    :param value: value to test
    :type value: str

    :return: whether the string represents False or not.
    :rtype: bool
    """
    return _truthiness.is_falsy(value)


class EnvironmentSource:
    """Resolves configuration values from environment variables.

    Example:
        >>> EnvironmentSource.get("HOME")
        '/home/user'
        >>> EnvironmentSource.get(None) is None
        True
    """

    @classmethod
    def get(cls, env_var: str | None) -> str | None:
        """Get the value of an environment variable.

        Args:
            env_var: Name of the environment variable to read.
                Returns None if env_var is None or empty.

        Returns:
            The environment variable value, or None if not set.
        """
        return _sources.from_environment(env_var)


class DictionarySource:
    """Resolves configuration values from nested dictionary structures.

    Handles two-level key paths into a JSON-like configuration dict,
    typically loaded from a YAML or JSON config file.

    Example:
        >>> source = {"openaev": {"url": "http://localhost:8080"}}
        >>> DictionarySource.get(["openaev", "url"], source)
        'http://localhost:8080'
    """

    @classmethod
    def get(
        cls, config_key_path: list[str] | None, source_dict: dict[str, Any]
    ) -> str | None:
        """Get a value from a nested dict using a two-level key path.

        Args:
            config_key_path: A list of exactly 2 non-empty strings representing
                the path ``[section, key]`` into the source dict.
            source_dict: The nested dictionary to search.

        Returns:
            The value at the specified path, or None if not found.

        Raises:
            AssertionError: If config_key_path is not a 2-element list of
                non-empty strings.
        """
        return _sources.from_dictionary(config_key_path, source_dict)


class ConnectorConfigSchemaGenerator(GenerateJsonSchema):
    """Custom JSON schema generator for connector configurations.

    Produces a flat schema where all config variables are at root level,
    with ``$ref`` entries fully resolved and filtered attributes removed.

    This is used by ``Configuration.schema()`` to produce manifests
    compatible with the OpenAEV platform connector registration API.
    """

    @staticmethod
    def dereference_schema(schema_with_refs: dict[str, Any]) -> dict[str, Any]:
        """Resolve all internal ``$ref`` entries in a JSON schema.

        Args:
            schema_with_refs: A JSON schema dict potentially containing
                ``$ref`` pointers to ``$defs``.

        Returns:
            A new schema with all references inlined.

        Raises:
            ValueError: If a ``$ref`` uses an unsupported format.
        """
        return _schema.dereference_schema(schema_with_refs)

    @staticmethod
    def flatten_config_loader_schema(root_schema: dict[str, Any]) -> dict[str, Any]:
        """Flatten a hierarchical config schema to root-level properties.

        Transforms nested namespace properties into flat
        ``NAMESPACE_VARIABLE`` format suitable for environment variable
        mapping.

        Args:
            root_schema: The dereferenced schema to flatten.

        Returns:
            A flat schema with all properties at root level.
        """
        return _schema.flatten_config_loader_schema(root_schema)

    @staticmethod
    def filter_schema(schema: dict[str, Any]) -> dict[str, Any]:
        """Remove filtered attributes from the schema.

        Args:
            schema: The flat schema to filter.

        Returns:
            The schema with filtered attributes removed.
        """
        return _schema.filter_schema(schema)

    @override
    def generate(self, schema: Any, mode: str = "validation") -> dict[str, Any]:
        """Generate a flat, dereferenced, filtered JSON schema.

        Args:
            schema: The Pydantic core schema to process.
            mode: Schema generation mode.

        Returns:
            The final connector configuration schema.
        """
        json_schema = super().generate(schema, mode=mode)
        return _schema.finalize(json_schema, self.schema_dialect)

    @override
    def nullable_schema(self, schema: Any) -> dict[str, Any]:
        """Generate schema for nullable fields without ``anyOf``.

        Overrides the default behavior to produce cleaner schemas
        that don't use the ``anyOf`` keyword for optional fields.

        Args:
            schema: The core schema for the nullable type.

        Returns:
            The generated JSON schema for the nullable type.
        """
        return _schema.collapse_nullable(self.generate_inner(schema["schema"]))


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
        self.__config_hints: dict[str, ConfigurationHint] = _resolver.build_hints(
            config_hints
        )
        self.__config_values = _resolver.load_values(config_values, config_file_path)
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

        return _resolver.resolve(config, self.__config_values)

    def set(self, config_key: str, value: CONFIGURATION_TYPES) -> None:
        """Set a runtime override for a configuration key.

        After calling this, ``get(config_key)`` will return the
        overridden value regardless of environment or file sources.

        Args:
            config_key: The configuration key to override.
            value: The new value to return for this key.
        """
        _resolver.override(self.__config_hints, config_key, value)

    def schema(self) -> dict[str, Any]:
        """Generate the connector configuration JSON schema.

        Uses the configured base model's Pydantic schema generation
        with the ConnectorConfigSchemaGenerator for flattened output.

        Returns:
            A JSON schema dict describing all configuration properties.

        Raises:
            AttributeError: If no config_base_model was provided.
        """
        return _resolver.generate_schema(
            self.__base_model, schema_generator=ConnectorConfigSchemaGenerator
        )


class SettingsLoader(BaseSettings):
    """Base settings class with prioritized multi-source loading.

    Automatically discovers and loads configuration from environment
    variables, YAML files, and .env files with a defined priority order.

    Subclass this to define your connector's configuration schema.

    Example:
        >>> class MySettings(SettingsLoader):
        ...     model_config = SettingsConfigDict(yaml_file="config.yml")
        ...     api_url: str
        ...     timeout: int = 30
    """

    model_config = SettingsConfigDict(
        frozen=True,
        extra="allow",
        env_nested_delimiter="_",
        env_nested_max_split=1,
        enable_decoding=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Configure source resolution order.

        Resolution priority:
            1. Environment variables (always checked first)
            2. YAML file (if config.yml exists)
            3. .env file (if .env exists and no YAML found)
            4. Default values (implicit via Pydantic)

        Args:
            settings_cls: The settings class being configured.
            init_settings: Init-based settings source.
            env_settings: Environment variable source.
            dotenv_settings: .env file source.
            file_secret_settings: Secrets file source.

        Returns:
            Tuple of settings sources in priority order.
        """
        return _settings_sources.select_sources(settings_cls, env_settings)
