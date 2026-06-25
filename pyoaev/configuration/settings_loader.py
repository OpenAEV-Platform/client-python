"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

warnings.warn(
    "Importing from 'pyoaev.configuration.settings_loader' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
    BaseConfigModel,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    HttpUrlToString,
    LogLevelToLower,
    SettingsLoader,
    TimedeltaInSeconds,
)

__all__ = [
    "BaseConfigModel",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "HttpUrlToString",
    "LogLevelToLower",
    "SettingsLoader",
    "TimedeltaInSeconds",
]
