"""Daemons seam: the contract between the public daemon runtime and the core.

The daemon consumer protocols (``DaemonProtocol``, ``BaseClient``) belong to
the common seam. Closed: it imports nothing from ``xtm_oaev_sdk._core`` nor
``xtm_oaev_sdk.public``. Any change to these contracts must bump
:data:`SEAM_VERSION`.
"""

from xtm_oaev_sdk.seam.daemons.ports import DaemonRuntimePort, HeartbeatPort

#: Version of the daemons seam. Bump on any contract change.
SEAM_VERSION = "1.0.0"

__all__ = ["SEAM_VERSION", "DaemonRuntimePort", "HeartbeatPort"]
