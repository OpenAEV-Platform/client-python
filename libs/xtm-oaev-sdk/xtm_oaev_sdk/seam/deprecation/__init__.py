"""Deprecation seam: the contract between the public deprecation adapter and
the core.

Closed: it imports nothing from ``xtm_oaev_sdk._core`` nor
``xtm_oaev_sdk.public``. Any change to these contracts must bump
:data:`SEAM_VERSION`.
"""

from xtm_oaev_sdk.seam.deprecation.ports import DeprecatedNames, DeprecationPort

#: Version of the deprecation seam. Bump on any contract change.
SEAM_VERSION = "1.0.0"

__all__ = ["SEAM_VERSION", "DeprecatedNames", "DeprecationPort"]
