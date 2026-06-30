"""Configuration management: loading, hints, and schema generation.

Re-exports the public configuration surface for internal engine use.
Public consumers import from xtm_oaev_sdk directly.
"""

from .configuration import (
    CONFIGURATION_TYPES,
    Configuration,
    ConfigurationHint,
    ConfigurationProtocol,
)
from .connector_config_schema_generator import ConnectorConfigSchemaGenerator
from .settings_loader import (
    BaseConfigModel,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    HttpUrlToString,
    LogLevelToLower,
    SettingsLoader,
    TimedeltaInSeconds,
)
from .sources import DictionarySource, EnvironmentSource

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
]
