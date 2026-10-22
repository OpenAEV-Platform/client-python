"""Configuration seam: the contract between the public adapters and the core.

Closed: it imports nothing from ``xtm_oaev_sdk._core`` nor
``xtm_oaev_sdk.public``. Any change to these contracts is a breaking change for
one side of the boundary and must bump :data:`SEAM_VERSION`.
"""

from xtm_oaev_sdk.seam.configuration.models import (
    CONFIGURATION_TYPES,
    BaseConfigModel,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    ConfigurationHint,
    HttpUrlToString,
    LogLevelToLower,
    TimedeltaInSeconds,
)
from xtm_oaev_sdk.seam.configuration.ports import (
    ConfigurationProtocol,
    ConfigurationResolverPort,
    ConfigurationSourcesPort,
    ConnectorSchemaPort,
    SettingsSourcesPort,
    TruthinessPort,
)

#: Version of the configuration seam. Bump on any contract change.
SEAM_VERSION = "1.0.0"

__all__ = [
    "SEAM_VERSION",
    # Data contracts
    "BaseConfigModel",
    "CONFIGURATION_TYPES",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "ConfigurationHint",
    "HttpUrlToString",
    "LogLevelToLower",
    "TimedeltaInSeconds",
    # Ports
    "ConfigurationProtocol",
    "ConfigurationResolverPort",
    "ConfigurationSourcesPort",
    "ConnectorSchemaPort",
    "SettingsSourcesPort",
    "TruthinessPort",
]
