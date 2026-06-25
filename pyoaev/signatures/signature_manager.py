"""Backward-compatibility shim for SignatureManager.

The SDK's SignatureManager now takes a ``SignatureTransportProtocol`` instead
of a concrete ``OpenAEV`` client. This shim preserves the original pyoaev
interface by adapting ``client.signature`` to the protocol.

Prefer direct SDK usage::

    from xtm_oaev_sdk import SignatureManager, SignatureTransportProtocol
"""

import logging
import warnings
from typing import TYPE_CHECKING

from xtm_oaev_sdk import (
    SignatureManager as _SDKSignatureManager,
    SignatureTransportProtocol,
)

if TYPE_CHECKING:
    from pyoaev.client import OpenAEV

warnings.warn(
    "Importing from 'pyoaev.signatures.signature_manager' is deprecated. "
    "Use 'from xtm_oaev_sdk import SignatureManager' with a "
    "SignatureTransportProtocol transport instead.",
    DeprecationWarning,
    stacklevel=2,
)


class SignatureManager(_SDKSignatureManager):
    """Backward-compatible SignatureManager accepting a pyoaev client.

    Adapts ``client.signature`` (which already implements
    SignatureTransportProtocol) as the transport layer.

    Args:
        client: The pyoaev OpenAEV client instance.
        logger: Optional logger. Defaults to module-level logger.
        max_payload_size: Maximum payload size in bytes.
    """

    def __init__(
        self,
        client: "OpenAEV",
        logger: logging.Logger | None = None,
        max_payload_size: int = _SDKSignatureManager.DEFAULT_MAX_PAYLOAD_SIZE,
    ) -> None:
        # client.signature implements SignatureTransportProtocol
        super().__init__(
            transport=client.signature,
            logger=logger,
            max_payload_size=max_payload_size,
        )
        # Keep reference for any code that accesses self.client directly
        self.client = client


__all__ = ["SignatureManager"]
