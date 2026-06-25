"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import ContractCardinality as _ContractCardinality
from xtm_oaev_sdk import ContractVariable as _ContractVariable
from xtm_oaev_sdk import VariableType as _VariableType

ContractCardinality = deprecated(
    "Use 'from xtm_oaev_sdk import ContractCardinality' instead.",
    category=DeprecationWarning,
)(_ContractCardinality)
ContractVariable = deprecated(
    "Use 'from xtm_oaev_sdk import ContractVariable' instead.",
    category=DeprecationWarning,
)(_ContractVariable)
VariableType = deprecated(
    "Use 'from xtm_oaev_sdk import VariableType' instead.",
    category=DeprecationWarning,
)(_VariableType)

__all__ = [
    "ContractCardinality",
    "ContractVariable",
    "VariableType",
]
