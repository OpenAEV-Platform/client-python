"""Backward-compatibility shim.

Prefer::

    from xtm_oaev_sdk import SignatureType
"""

import warnings

warnings.warn(
    "Importing from 'pyoaev.signatures.signature_type' is deprecated. "
    "Use 'from xtm_oaev_sdk import SignatureType' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import SignatureType

__all__ = ["SignatureType"]
