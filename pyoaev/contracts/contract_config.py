"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

warnings.warn(
    "Importing from 'pyoaev.contracts.contract_config' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
    Contract,
    ContractAsset,
    ContractAssetGroup,
    ContractAttachment,
    ContractCardinalityElement,
    ContractCheckbox,
    ContractConfig,
    ContractElement,
    ContractExpectationType,
    ContractExpectations,
    ContractFieldKey,
    ContractFieldType,
    ContractOutputElement,
    ContractOutputType,
    ContractPayload,
    ContractSelect,
    ContractTeam,
    ContractText,
    ContractTextArea,
    ContractTuple,
    Domain,
    Expectation,
    LinkedFieldModel,
    SupportedLanguage,
    prepare_contracts,
)

__all__ = [
    "Contract",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAttachment",
    "ContractCardinalityElement",
    "ContractCheckbox",
    "ContractConfig",
    "ContractElement",
    "ContractExpectationType",
    "ContractExpectations",
    "ContractFieldKey",
    "ContractFieldType",
    "ContractOutputElement",
    "ContractOutputType",
    "ContractPayload",
    "ContractSelect",
    "ContractTeam",
    "ContractText",
    "ContractTextArea",
    "ContractTuple",
    "Domain",
    "Expectation",
    "LinkedFieldModel",
    "SupportedLanguage",
    "prepare_contracts",
]
