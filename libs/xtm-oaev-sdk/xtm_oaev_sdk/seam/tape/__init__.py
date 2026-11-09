"""Call tape seam: record a daemon's outside calls to a tape, replay them offline.

Closed: it imports nothing from ``xtm_oaev_sdk._core`` nor ``xtm_oaev_sdk.public``.
Any change to these contracts must bump :data:`SEAM_VERSION`.
"""

from xtm_oaev_sdk.seam.tape.models import (
    TAPE_VERSION,
    Tape,
    TapedBody,
    TapedCall,
    TapedCommand,
    TapedHttpCall,
    TapedHttpRequest,
    TapedHttpResponse,
    TapeMissError,
)
from xtm_oaev_sdk.seam.tape.ports import CallTapePort

#: Version of the call tape seam. Bump on any contract change.
SEAM_VERSION = "1.0.0"

__all__ = [
    "SEAM_VERSION",
    "TAPE_VERSION",
    "CallTapePort",
    "Tape",
    "TapeMissError",
    "TapedBody",
    "TapedCall",
    "TapedCommand",
    "TapedHttpCall",
    "TapedHttpRequest",
    "TapedHttpResponse",
]
