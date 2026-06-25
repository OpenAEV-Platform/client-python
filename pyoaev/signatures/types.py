"""Backward-compatibility shim.

All symbols have moved to ``xtm_oaev_sdk``. This module re-exports them.
Prefer direct imports::

    from xtm_oaev_sdk import SignatureExpectationType, InjectExecutionActions, ...

Note: ``ExpectationType`` was renamed to ``SignatureExpectationType`` in the SDK.
The old name is preserved here as an alias for backward compatibility.
"""

import warnings

warnings.warn(
    "Importing from 'pyoaev.signatures.types' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead. "
    "Note: ExpectationType is now SignatureExpectationType.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
    InjectExecutionActions,
    MatchTypes,
    SignatureExpectationType,
    SignatureTypes,
)

# Backward-compat alias for the renamed enum
ExpectationType = SignatureExpectationType

__all__ = [
    "ExpectationType",
    "InjectExecutionActions",
    "MatchTypes",
    "SignatureExpectationType",
    "SignatureTypes",
]
