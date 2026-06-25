"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import ContractBuilder as _ContractBuilder

ContractBuilder = deprecated(
    "Use 'from xtm_oaev_sdk import ContractBuilder' instead.",
    category=DeprecationWarning,
)(_ContractBuilder)

__all__ = [
    "ContractBuilder",
]
