"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

import warnings

warnings.warn(
    "Importing from 'pyoaev.configuration.connector_config_schema_generator' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import ConnectorConfigSchemaGenerator

__all__ = [
    "ConnectorConfigSchemaGenerator",
]
