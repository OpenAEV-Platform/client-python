"""Public surface for the signatures subpackage.

This module re-exports the canonical signature types, models, and manager
protocols used by the SDK engine signatures package.
"""

from .models import (
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
from .signature_manager import (
    SignatureManager,
    SignatureManagerProtocol,
    SignatureTransportProtocol,
)
from .signature_match import SignatureMatch
from .signature_type import SignatureType
from .types import (
    InjectExecutionActions,
    MatchTypes,
    SignatureExpectationType,
    SignatureTypes,
)

__all__ = [
    "CloudInjectorConfig",
    "ExecutionDetails",
    "ExecutionSignature",
    "ExpectationSignatureGroup",
    "ExtraSignatureData",
    "InjectExecutionActions",
    "InjectorConfig",
    "MatchTypes",
    "NetworkInjectorConfig",
    "SignatureCallbackPayload",
    "SignatureExpectationType",
    "SignatureManager",
    "SignatureManagerProtocol",
    "SignatureMatch",
    "SignatureOutputStructure",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureTransportProtocol",
    "SignatureType",
    "SignatureTypes",
    "SignatureValue",
    "TargetSignatures",
    "ToolErrorInfo",
    "ToolOutput",
    "ToolTimeoutInfo",
    "build_network_configs",
]
