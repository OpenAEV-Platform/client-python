"""Backward-compat shim for SignatureManager.

The SDK's SignatureManager now takes a ``SignatureTransportProtocol`` instead
of a concrete ``OpenAEV`` client. This shim preserves the original pyoaev
interface by adapting ``client.signature`` to the protocol.

Prefer direct SDK usage::

    from xtm_oaev_sdk import SignatureManager, SignatureTransportProtocol
"""

import logging
from typing import TYPE_CHECKING

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    SignatureManager as _SDKSignatureManager,
    SignatureTransportProtocol,
)

if TYPE_CHECKING:
    from pyoaev.client import OpenAEV


@deprecated(
    "Use 'from xtm_oaev_sdk import SignatureManager' with a "
    "SignatureTransportProtocol transport instead.",
    category=DeprecationWarning,
)
class SignatureManager(_SDKSignatureManager):
    """Backward-compatible SignatureManager accepting a pyoaev client.

    Adapts ``client.signature`` (which already implements
    SignatureTransportProtocol) as the transport layer.
    """

    def __init__(
        self,
        client: "OpenAEV",
        logger: logging.Logger | None = None,
        max_payload_size: int = _SDKSignatureManager.DEFAULT_MAX_PAYLOAD_SIZE,
    ) -> None:
        super().__init__(
            transport=client.signature,
            logger=logger,
            max_payload_size=max_payload_size,
        )
        self.client = client


__all__ = ["SignatureManager"]
