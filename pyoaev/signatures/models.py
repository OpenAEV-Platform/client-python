"""Backward-compatibility shim.

All symbols have moved to ``xtm_oaev_sdk``. This module re-exports them.
Prefer direct imports::

    from xtm_oaev_sdk import SignaturePayload, ExecutionDetails, ...
"""

import warnings

warnings.warn(
    "Importing from 'pyoaev.signatures.models' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
    CloudInjectorConfig,
    ExecutionDetails,
    ExecutionSignature,
    ExpectationSignatureGroup,
    ExtraSignatureData,
    InjectorConfig,
    NetworkInjectorConfig,
    SignatureCallbackPayload,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
    build_network_configs,
)

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
