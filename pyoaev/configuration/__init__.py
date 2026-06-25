"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    BaseConfigModel as _BaseConfigModel,
    Configuration as _Configuration,
    ConfigLoaderCollector as _ConfigLoaderCollector,
    ConfigLoaderOAEV as _ConfigLoaderOAEV,
    SettingsLoader as _SettingsLoader,
)

BaseConfigModel = deprecated("Use 'from xtm_oaev_sdk import BaseConfigModel' instead.", category=DeprecationWarning)(_BaseConfigModel)
Configuration = deprecated("Use 'from xtm_oaev_sdk import Configuration' instead.", category=DeprecationWarning)(_Configuration)
ConfigLoaderCollector = deprecated("Use 'from xtm_oaev_sdk import ConfigLoaderCollector' instead.", category=DeprecationWarning)(_ConfigLoaderCollector)
ConfigLoaderOAEV = deprecated("Use 'from xtm_oaev_sdk import ConfigLoaderOAEV' instead.", category=DeprecationWarning)(_ConfigLoaderOAEV)
SettingsLoader = deprecated("Use 'from xtm_oaev_sdk import SettingsLoader' instead.", category=DeprecationWarning)(_SettingsLoader)

__all__ = [
    "BaseConfigModel",
    "Configuration",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "SettingsLoader",
]
