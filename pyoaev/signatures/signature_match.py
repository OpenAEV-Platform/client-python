"""Backward-compatibility shim.

Prefer::

    from xtm_oaev_sdk import SignatureMatch
"""

import warnings

warnings.warn(
    "Importing from 'pyoaev.signatures.signature_match' is deprecated. "
    "Use 'from xtm_oaev_sdk import SignatureMatch' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import SignatureMatch

__all__ = ["SignatureMatch"]
