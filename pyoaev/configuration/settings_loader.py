"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    BaseConfigModel as _BaseConfigModel,
    ConfigLoaderCollector as _ConfigLoaderCollector,
    ConfigLoaderOAEV as _ConfigLoaderOAEV,
    SettingsLoader as _SettingsLoader,
)
import xtm_oaev_sdk as _sdk

BaseConfigModel = deprecated("Use 'from xtm_oaev_sdk import BaseConfigModel' instead.", category=DeprecationWarning)(_BaseConfigModel)
ConfigLoaderCollector = deprecated("Use 'from xtm_oaev_sdk import ConfigLoaderCollector' instead.", category=DeprecationWarning)(_ConfigLoaderCollector)
ConfigLoaderOAEV = deprecated("Use 'from xtm_oaev_sdk import ConfigLoaderOAEV' instead.", category=DeprecationWarning)(_ConfigLoaderOAEV)
SettingsLoader = deprecated("Use 'from xtm_oaev_sdk import SettingsLoader' instead.", category=DeprecationWarning)(_SettingsLoader)

_NON_DECORATABLE = {"HttpUrlToString", "LogLevelToLower", "TimedeltaInSeconds"}

def __getattr__(name: str):
    if name in _NON_DECORATABLE:
        warnings.warn(
            f"Use 'from xtm_oaev_sdk import {name}' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(_sdk, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "BaseConfigModel",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "HttpUrlToString",
    "LogLevelToLower",
    "SettingsLoader",
    "TimedeltaInSeconds",
]
