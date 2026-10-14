"""Contracts seam: the contract between the public adapters and the core.

Closed: it imports nothing from ``xtm_oaev_sdk._core`` nor
``xtm_oaev_sdk.public``. Any change to these contracts is a breaking change for
one side of the boundary and must bump :data:`SEAM_VERSION`.
"""

from xtm_oaev_sdk.seam.contracts.models import (
    ContractAiTarget,
    ContractAsset,
    ContractAssetGroup,
    ContractAttachment,
    ContractCardinality,
    ContractCardinalityElement,
    ContractCheckbox,
    ContractConfig,
    ContractData,
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
    ContractVariable,
    CredentialType,
    Domain,
    Expectation,
    LinkedFieldModel,
    PrimitiveType,
    SecurityPlatformType,
    SupportedLanguage,
    VariableType,
)
from xtm_oaev_sdk.seam.contracts.ports import (
    ContractAssemblyPort,
    ContractBuilderProtocol,
    ContractCredentialsPort,
    ContractSerializerPort,
    ContractVariablesPort,
)

#: Version of the contracts seam. Bump on any contract change.
SEAM_VERSION = "1.0.0"

__all__ = [
    "SEAM_VERSION",
    # Data contracts
    "ContractAiTarget",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAttachment",
    "ContractCardinality",
    "ContractCardinalityElement",
    "ContractCheckbox",
    "ContractConfig",
    "ContractData",
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
    "VariableType",
    # Ports
    "ContractAssemblyPort",
    "ContractBuilderProtocol",
    "ContractCredentialsPort",
    "ContractSerializerPort",
    "ContractVariablesPort",
]
