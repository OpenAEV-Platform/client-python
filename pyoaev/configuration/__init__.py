"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

warnings.warn(
    "Importing from 'pyoaev.configuration' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
    BaseConfigModel,
    Configuration,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    SettingsLoader,
)

__all__ = [
    "BaseConfigModel",
    "Configuration",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "SettingsLoader",
]
