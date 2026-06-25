"""Backward-compat shim — use 'from xtm_oaev_sdk import SignatureType' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import SignatureType as _SignatureType

SignatureType = deprecated("Use 'from xtm_oaev_sdk import SignatureType' instead.", category=DeprecationWarning)(_SignatureType)

__all__ = ["SignatureType"]
