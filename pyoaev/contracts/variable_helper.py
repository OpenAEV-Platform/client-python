"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import VariableHelper as _VariableHelper

VariableHelper = deprecated(
    "Use 'from xtm_oaev_sdk import VariableHelper' instead.",
    category=DeprecationWarning,
)(_VariableHelper)

__all__ = [
    "VariableHelper",
]
