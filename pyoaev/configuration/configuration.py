"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    Configuration as _Configuration,
    ConfigurationHint as _ConfigurationHint,
    ConfigurationProtocol as _ConfigurationProtocol,
)
import xtm_oaev_sdk as _sdk

Configuration = deprecated("Use 'from xtm_oaev_sdk import Configuration' instead.", category=DeprecationWarning)(_Configuration)
ConfigurationHint = deprecated("Use 'from xtm_oaev_sdk import ConfigurationHint' instead.", category=DeprecationWarning)(_ConfigurationHint)
ConfigurationProtocol = deprecated("Use 'from xtm_oaev_sdk import ConfigurationProtocol' instead.", category=DeprecationWarning)(_ConfigurationProtocol)

_NON_DECORATABLE = {"CONFIGURATION_TYPES"}

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
    "CONFIGURATION_TYPES",
    "Configuration",
    "ConfigurationHint",
    "ConfigurationProtocol",
]
