"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    DictionarySource as _DictionarySource,
    EnvironmentSource as _EnvironmentSource,
)

DictionarySource = deprecated("Use 'from xtm_oaev_sdk import DictionarySource' instead.", category=DeprecationWarning)(_DictionarySource)
EnvironmentSource = deprecated("Use 'from xtm_oaev_sdk import EnvironmentSource' instead.", category=DeprecationWarning)(_EnvironmentSource)

__all__ = [
    "DictionarySource",
    "EnvironmentSource",
]
