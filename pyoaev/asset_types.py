"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    AssetCategory as _AssetCategory,
    AssetCriticality as _AssetCriticality,
    AssetSubCategory as _AssetSubCategory,
    CloudProvider as _CloudProvider,
)

AssetCategory = deprecated("Use 'from xtm_oaev_sdk import AssetCategory' instead.", category=DeprecationWarning)(_AssetCategory)
AssetCriticality = deprecated("Use 'from xtm_oaev_sdk import AssetCriticality' instead.", category=DeprecationWarning)(_AssetCriticality)
AssetSubCategory = deprecated("Use 'from xtm_oaev_sdk import AssetSubCategory' instead.", category=DeprecationWarning)(_AssetSubCategory)
CloudProvider = deprecated("Use 'from xtm_oaev_sdk import CloudProvider' instead.", category=DeprecationWarning)(_CloudProvider)

__all__ = [
    "AssetCategory",
    "AssetCriticality",
    "AssetSubCategory",
    "CloudProvider",
]
