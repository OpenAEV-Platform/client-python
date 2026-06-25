"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead.

Note: ``ExpectationType`` was renamed to ``SignatureExpectationType`` in the SDK.
The old name is preserved here as a deprecated alias.
"""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    InjectExecutionActions as _InjectExecutionActions,
    MatchTypes as _MatchTypes,
    SignatureExpectationType as _SignatureExpectationType,
    SignatureTypes as _SignatureTypes,
)

InjectExecutionActions = deprecated("Use 'from xtm_oaev_sdk import InjectExecutionActions' instead.", category=DeprecationWarning)(_InjectExecutionActions)
MatchTypes = deprecated("Use 'from xtm_oaev_sdk import MatchTypes' instead.", category=DeprecationWarning)(_MatchTypes)
SignatureExpectationType = deprecated("Use 'from xtm_oaev_sdk import SignatureExpectationType' instead.", category=DeprecationWarning)(_SignatureExpectationType)
SignatureTypes = deprecated("Use 'from xtm_oaev_sdk import SignatureTypes' instead.", category=DeprecationWarning)(_SignatureTypes)

# Backward-compat alias for renamed enum
ExpectationType = deprecated("Use 'from xtm_oaev_sdk import SignatureExpectationType' instead. 'ExpectationType' was renamed.", category=DeprecationWarning)(_SignatureExpectationType)

__all__ = [
    "ExpectationType",
    "InjectExecutionActions",
    "MatchTypes",
    "SignatureExpectationType",
    "SignatureTypes",
]
