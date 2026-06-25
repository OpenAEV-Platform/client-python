"""Backward-compatibility shim for pyoaev.signatures.

All symbols have moved to ``xtm_oaev_sdk``. This barrel re-exports them.
Prefer direct imports::

    from xtm_oaev_sdk import SignatureManager, SignatureExpectationType, ...

Note: ``ExpectationType`` has been renamed to ``SignatureExpectationType``.
The old name is preserved here as an alias.
"""

import warnings

warnings.warn(
    "Importing from 'pyoaev.signatures' is deprecated. "
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
    InjectExecutionActions,
    MatchTypes,
    NetworkInjectorConfig,
    SignatureCallbackPayload,
    SignatureExpectationType,
    SignatureManager,
    SignatureMatch,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureType,
    SignatureTypes,
    SignatureValue,
    TargetSignatures,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
    build_network_configs,
)

# Backward-compat alias
ExpectationType = SignatureExpectationType

__all__ = [
    "CloudInjectorConfig",
    "ExecutionDetails",
    "ExecutionSignature",
    "ExpectationSignatureGroup",
    "ExpectationType",
    "ExtraSignatureData",
    "InjectorConfig",
    "InjectExecutionActions",
    "MatchTypes",
    "NetworkInjectorConfig",
    "SignatureCallbackPayload",
    "SignatureExpectationType",
    "SignatureManager",
    "SignatureMatch",
    "SignatureOutputStructure",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureType",
    "SignatureTypes",
    "SignatureValue",
    "TargetSignatures",
    "ToolErrorInfo",
    "ToolOutput",
    "ToolTimeoutInfo",
    "build_network_configs",
]
