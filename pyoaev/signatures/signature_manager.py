"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

The SDK ``SignatureManager`` takes a ``SignatureTransportProtocol`` instead of
an ``OpenAEV`` client. The legacy name resolves to a thin subclass that keeps
the historical ``SignatureManager(client, logger=None, max_payload_size=...)``
constructor by using ``client.signature`` as the transport. Every other name
resolves to the *identical* xtm_oaev_sdk object. All names emit a
:class:`DeprecationWarning` on access.

``socket`` and ``subprocess`` stay importable here so that legacy patch targets
such as ``pyoaev.signatures.signature_manager.socket.gethostbyname`` keep
reaching the shared standard-library modules the SDK uses.
"""

import socket  # noqa: F401
import subprocess  # noqa: F401
from typing import TYPE_CHECKING

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

if TYPE_CHECKING:
    from pyoaev.client import OpenAEV


class _ClientSignatureManager(_sdk.SignatureManager):
    """SDK SignatureManager driven by a pyoaev client (legacy constructor)."""

    def __init__(
        self,
        client: "OpenAEV",
        logger=None,
        max_payload_size: int = _sdk.SignatureManager.DEFAULT_MAX_PAYLOAD_SIZE,
    ) -> None:
        super().__init__(
            transport=client.signature,
            logger=logger,
            max_payload_size=max_payload_size,
        )
        self.client = client


__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "SignatureManager",
    "OpenAEVError",
    "CloudInjectorConfig",
    "ExecutionDetails",
    "ExecutionSignature",
    "ExpectationSignatureGroup",
    "ExtraSignatureData",
    "InjectorConfig",
    "NetworkInjectorConfig",
    "SignatureOutputStructure",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureValue",
    "TargetSignatures",
    "ToolOutput",
]

__getattr__ = _make_deprecated_getattr(
    {
        "SignatureManager": (
            "Use 'from xtm_oaev_sdk import SignatureManager' with a "
            "SignatureTransportProtocol transport (e.g. client.signature) instead.",
            _ClientSignatureManager,
        ),
        **{
            name: (
                f"Use 'from xtm_oaev_sdk import {name}' instead.",
                getattr(_sdk, name),
            )
            for name in __all__
            if name != "SignatureManager"
        },
    },
    module_name=__name__,
)
