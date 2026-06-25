"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import ContractBuilder as _ContractBuilder
from xtm_oaev_sdk import ContractBuilderProtocol as _ContractBuilderProtocol

ContractBuilder = deprecated(
    "Use 'from xtm_oaev_sdk import ContractBuilder' instead.",
    category=DeprecationWarning,
)(_ContractBuilder)
ContractBuilderProtocol = deprecated(
    "Use 'from xtm_oaev_sdk import ContractBuilderProtocol' instead.",
    category=DeprecationWarning,
)(_ContractBuilderProtocol)

__all__ = [
    "ContractBuilder",
    "ContractBuilderProtocol",
]
