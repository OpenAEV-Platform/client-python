"""Public API surface for xtm-oaev-sdk."""

__version__ = "0.1.0"

# --- Configuration ---
from xtm_oaev_sdk.seam.configuration import (
    CONFIGURATION_TYPES,
    BaseConfigModel,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    Configuration,
    ConfigurationHint,
    ConfigurationProtocol,
    ConnectorConfigSchemaGenerator,
    DictionarySource,
    EnvironmentSource,
    HttpUrlToString,
    LogLevelToLower,
    SettingsLoader,
    TimedeltaInSeconds,
    is_falsy,
    is_truthy,
)

# --- Seam / compatibility ---
from xtm_oaev_sdk.seam.deprecation import make_deprecated_getattr

__all__ = [
    "__version__",
    # Configuration
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
    # Seam / compatibility
    "make_deprecated_getattr",
]
