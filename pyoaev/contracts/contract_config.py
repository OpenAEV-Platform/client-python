"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    Contract as _Contract,
    ContractAsset as _ContractAsset,
    ContractAssetGroup as _ContractAssetGroup,
    ContractAttachment as _ContractAttachment,
    ContractCardinalityElement as _ContractCardinalityElement,
    ContractCheckbox as _ContractCheckbox,
    ContractConfig as _ContractConfig,
    ContractElement as _ContractElement,
    ContractExpectationType as _ContractExpectationType,
    ContractExpectations as _ContractExpectations,
    ContractFieldKey as _ContractFieldKey,
    ContractFieldType as _ContractFieldType,
    ContractOutputElement as _ContractOutputElement,
    ContractOutputType as _ContractOutputType,
    ContractPayload as _ContractPayload,
    ContractSelect as _ContractSelect,
    ContractTeam as _ContractTeam,
    ContractText as _ContractText,
    ContractTextArea as _ContractTextArea,
    ContractTuple as _ContractTuple,
    Domain as _Domain,
    Expectation as _Expectation,
    LinkedFieldModel as _LinkedFieldModel,
    SupportedLanguage as _SupportedLanguage,
    prepare_contracts as _prepare_contracts,
)

Contract = deprecated("Use 'from xtm_oaev_sdk import Contract' instead.", category=DeprecationWarning)(_Contract)
ContractAsset = deprecated("Use 'from xtm_oaev_sdk import ContractAsset' instead.", category=DeprecationWarning)(_ContractAsset)
ContractAssetGroup = deprecated("Use 'from xtm_oaev_sdk import ContractAssetGroup' instead.", category=DeprecationWarning)(_ContractAssetGroup)
ContractAttachment = deprecated("Use 'from xtm_oaev_sdk import ContractAttachment' instead.", category=DeprecationWarning)(_ContractAttachment)
ContractCardinalityElement = deprecated("Use 'from xtm_oaev_sdk import ContractCardinalityElement' instead.", category=DeprecationWarning)(_ContractCardinalityElement)
ContractCheckbox = deprecated("Use 'from xtm_oaev_sdk import ContractCheckbox' instead.", category=DeprecationWarning)(_ContractCheckbox)
ContractConfig = deprecated("Use 'from xtm_oaev_sdk import ContractConfig' instead.", category=DeprecationWarning)(_ContractConfig)
ContractElement = deprecated("Use 'from xtm_oaev_sdk import ContractElement' instead.", category=DeprecationWarning)(_ContractElement)
ContractExpectationType = deprecated("Use 'from xtm_oaev_sdk import ContractExpectationType' instead.", category=DeprecationWarning)(_ContractExpectationType)
ContractExpectations = deprecated("Use 'from xtm_oaev_sdk import ContractExpectations' instead.", category=DeprecationWarning)(_ContractExpectations)
ContractFieldKey = deprecated("Use 'from xtm_oaev_sdk import ContractFieldKey' instead.", category=DeprecationWarning)(_ContractFieldKey)
ContractFieldType = deprecated("Use 'from xtm_oaev_sdk import ContractFieldType' instead.", category=DeprecationWarning)(_ContractFieldType)
ContractOutputElement = deprecated("Use 'from xtm_oaev_sdk import ContractOutputElement' instead.", category=DeprecationWarning)(_ContractOutputElement)
ContractOutputType = deprecated("Use 'from xtm_oaev_sdk import ContractOutputType' instead.", category=DeprecationWarning)(_ContractOutputType)
ContractPayload = deprecated("Use 'from xtm_oaev_sdk import ContractPayload' instead.", category=DeprecationWarning)(_ContractPayload)
ContractSelect = deprecated("Use 'from xtm_oaev_sdk import ContractSelect' instead.", category=DeprecationWarning)(_ContractSelect)
ContractTeam = deprecated("Use 'from xtm_oaev_sdk import ContractTeam' instead.", category=DeprecationWarning)(_ContractTeam)
ContractText = deprecated("Use 'from xtm_oaev_sdk import ContractText' instead.", category=DeprecationWarning)(_ContractText)
ContractTextArea = deprecated("Use 'from xtm_oaev_sdk import ContractTextArea' instead.", category=DeprecationWarning)(_ContractTextArea)
ContractTuple = deprecated("Use 'from xtm_oaev_sdk import ContractTuple' instead.", category=DeprecationWarning)(_ContractTuple)
Domain = deprecated("Use 'from xtm_oaev_sdk import Domain' instead.", category=DeprecationWarning)(_Domain)
Expectation = deprecated("Use 'from xtm_oaev_sdk import Expectation' instead.", category=DeprecationWarning)(_Expectation)
LinkedFieldModel = deprecated("Use 'from xtm_oaev_sdk import LinkedFieldModel' instead.", category=DeprecationWarning)(_LinkedFieldModel)
SupportedLanguage = deprecated("Use 'from xtm_oaev_sdk import SupportedLanguage' instead.", category=DeprecationWarning)(_SupportedLanguage)
prepare_contracts = deprecated("Use 'from xtm_oaev_sdk import prepare_contracts' instead.", category=DeprecationWarning)(_prepare_contracts)

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
