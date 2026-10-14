"""Contract building: field definitions, validation, and serialization.

Re-exports the public contract surface for internal engine use.
Public consumers import from xtm_oaev_sdk directly.
"""

from .contract_builder import ContractBuilder, ContractBuilderProtocol
from .contract_config import (
    Contract,
    ContractAiTarget,
    ContractAsset,
    ContractAssetGroup,
    ContractAttachment,
    ContractCardinalityElement,
    ContractCheckbox,
    ContractConfig,
    ContractElement,
    ContractExpectations,
    ContractExpectationType,
    ContractFieldKey,
    ContractFieldType,
    ContractOutputElement,
    ContractOutputType,
    ContractPayload,
    ContractReferencedCredential,
    ContractSelect,
    ContractTeam,
    ContractText,
    ContractTextArea,
    ContractTuple,
    Domain,
    Expectation,
    LinkedFieldModel,
    PrimitiveType,
    SecurityPlatformType,
    SupportedLanguage,
    prepare_contracts,
)
from .contract_utils import ContractCardinality, ContractVariable, VariableType
from .credential_types import CredentialType
from .credentials import build_single_referenced_credential_element
from .variable_helper import VariableHelper

__all__ = [
    "Contract",
    "ContractAiTarget",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAttachment",
    "ContractBuilder",
    "ContractBuilderProtocol",
    "ContractCardinality",
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
    "ContractReferencedCredential",
    "ContractSelect",
    "ContractTeam",
    "ContractText",
    "ContractTextArea",
    "ContractTuple",
    "ContractVariable",
    "CredentialType",
    "Domain",
    "Expectation",
    "LinkedFieldModel",
    "PrimitiveType",
    "SecurityPlatformType",
    "SupportedLanguage",
    "VariableHelper",
    "VariableType",
    "build_single_referenced_credential_element",
    "prepare_contracts",
]
