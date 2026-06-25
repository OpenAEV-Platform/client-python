"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    CloudInjectorConfig as _CloudInjectorConfig,
    ExecutionDetails as _ExecutionDetails,
    ExecutionSignature as _ExecutionSignature,
    ExpectationSignatureGroup as _ExpectationSignatureGroup,
    ExtraSignatureData as _ExtraSignatureData,
    NetworkInjectorConfig as _NetworkInjectorConfig,
    SignatureCallbackPayload as _SignatureCallbackPayload,
    SignatureOutputStructure as _SignatureOutputStructure,
    SignaturePayload as _SignaturePayload,
    SignatureTarget as _SignatureTarget,
    SignatureValue as _SignatureValue,
    TargetSignatures as _TargetSignatures,
    ToolErrorInfo as _ToolErrorInfo,
    ToolOutput as _ToolOutput,
    ToolTimeoutInfo as _ToolTimeoutInfo,
    build_network_configs as _build_network_configs,
)
import xtm_oaev_sdk as _sdk

CloudInjectorConfig = deprecated("Use 'from xtm_oaev_sdk import CloudInjectorConfig' instead.", category=DeprecationWarning)(_CloudInjectorConfig)
ExecutionDetails = deprecated("Use 'from xtm_oaev_sdk import ExecutionDetails' instead.", category=DeprecationWarning)(_ExecutionDetails)
ExecutionSignature = deprecated("Use 'from xtm_oaev_sdk import ExecutionSignature' instead.", category=DeprecationWarning)(_ExecutionSignature)
ExpectationSignatureGroup = deprecated("Use 'from xtm_oaev_sdk import ExpectationSignatureGroup' instead.", category=DeprecationWarning)(_ExpectationSignatureGroup)
ExtraSignatureData = deprecated("Use 'from xtm_oaev_sdk import ExtraSignatureData' instead.", category=DeprecationWarning)(_ExtraSignatureData)
NetworkInjectorConfig = deprecated("Use 'from xtm_oaev_sdk import NetworkInjectorConfig' instead.", category=DeprecationWarning)(_NetworkInjectorConfig)
SignatureCallbackPayload = deprecated("Use 'from xtm_oaev_sdk import SignatureCallbackPayload' instead.", category=DeprecationWarning)(_SignatureCallbackPayload)
SignatureOutputStructure = deprecated("Use 'from xtm_oaev_sdk import SignatureOutputStructure' instead.", category=DeprecationWarning)(_SignatureOutputStructure)
SignaturePayload = deprecated("Use 'from xtm_oaev_sdk import SignaturePayload' instead.", category=DeprecationWarning)(_SignaturePayload)
SignatureTarget = deprecated("Use 'from xtm_oaev_sdk import SignatureTarget' instead.", category=DeprecationWarning)(_SignatureTarget)
SignatureValue = deprecated("Use 'from xtm_oaev_sdk import SignatureValue' instead.", category=DeprecationWarning)(_SignatureValue)
TargetSignatures = deprecated("Use 'from xtm_oaev_sdk import TargetSignatures' instead.", category=DeprecationWarning)(_TargetSignatures)
ToolErrorInfo = deprecated("Use 'from xtm_oaev_sdk import ToolErrorInfo' instead.", category=DeprecationWarning)(_ToolErrorInfo)
ToolOutput = deprecated("Use 'from xtm_oaev_sdk import ToolOutput' instead.", category=DeprecationWarning)(_ToolOutput)
ToolTimeoutInfo = deprecated("Use 'from xtm_oaev_sdk import ToolTimeoutInfo' instead.", category=DeprecationWarning)(_ToolTimeoutInfo)
build_network_configs = deprecated("Use 'from xtm_oaev_sdk import build_network_configs' instead.", category=DeprecationWarning)(_build_network_configs)

# InjectorConfig is a UnionType — cannot be decorated with @deprecated.
InjectorConfig = _sdk.InjectorConfig

__all__ = [
    "CloudInjectorConfig",
    "ExecutionDetails",
    "ExecutionSignature",
    "ExpectationSignatureGroup",
    "ExtraSignatureData",
    "InjectorConfig",
    "NetworkInjectorConfig",
    "SignatureCallbackPayload",
    "SignatureOutputStructure",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureValue",
    "TargetSignatures",
    "ToolErrorInfo",
    "ToolOutput",
    "ToolTimeoutInfo",
    "build_network_configs",
]
