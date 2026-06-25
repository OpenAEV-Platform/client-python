"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

warnings.warn(
    "Importing from 'pyoaev.configuration.configuration' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
    CONFIGURATION_TYPES,
    Configuration,
    ConfigurationHint,
    ConfigurationProtocol,
)

__all__ = [
    "CONFIGURATION_TYPES",
    "Configuration",
    "ConfigurationHint",
    "ConfigurationProtocol",
]
