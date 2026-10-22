"""Signatures seam: the contract between the public adapters and the core.

The inbound I/O models (``seam.py``, versioned :data:`SEAM_VERSION` and
schema-pinned), the matching vocabulary and policies, and the signature ports.
The wire models live in :mod:`xtm_oaev_sdk.seam.port_io`. Closed: it imports
nothing from ``xtm_oaev_sdk._core`` nor ``xtm_oaev_sdk.public``.
"""

from xtm_oaev_sdk.seam.signatures.models import (
    ExtraSignatureData,
    MatchTypes,
    SignatureMatch,
    SignatureType,
    SignatureTypes,
)
from xtm_oaev_sdk.seam.signatures.ports import (
    ContainerAddressPort,
    MarkerPort,
    NetworkTargetsPort,
    SignatureEnginePort,
    SignatureManagerProtocol,
    SignatureTransportProtocol,
)
from xtm_oaev_sdk.seam.signatures.seam import (
    SEAM_VERSION,
    CloudInjectorConfig,
    ExecutionSignature,
    InjectorConfig,
    NetworkInjectorConfig,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
)

__all__ = [
    "SEAM_VERSION",
    # Inbound I/O models (seam.py)
    "CloudInjectorConfig",
    "ExecutionSignature",
    "InjectorConfig",
    "NetworkInjectorConfig",
    "ToolErrorInfo",
    "ToolOutput",
    "ToolTimeoutInfo",
    # Data contracts
    "ExtraSignatureData",
    "MatchTypes",
    "SignatureMatch",
    "SignatureType",
    "SignatureTypes",
    # Ports
    "ContainerAddressPort",
    "MarkerPort",
    "NetworkTargetsPort",
    "SignatureEnginePort",
    "SignatureManagerProtocol",
    "SignatureTransportProtocol",
]
