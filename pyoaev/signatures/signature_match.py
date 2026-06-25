"""Backward-compat shim — use 'from xtm_oaev_sdk import SignatureMatch' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import SignatureMatch as _SignatureMatch

SignatureMatch = deprecated("Use 'from xtm_oaev_sdk import SignatureMatch' instead.", category=DeprecationWarning)(_SignatureMatch)

__all__ = ["SignatureMatch"]
