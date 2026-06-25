"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import ConnectorConfigSchemaGenerator as _ConnectorConfigSchemaGenerator

ConnectorConfigSchemaGenerator = deprecated("Use 'from xtm_oaev_sdk import ConnectorConfigSchemaGenerator' instead.", category=DeprecationWarning)(_ConnectorConfigSchemaGenerator)

__all__ = [
    "ConnectorConfigSchemaGenerator",
]
