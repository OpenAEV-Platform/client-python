# -*- coding: utf-8 -*-
__version__ = "2.260627.0"

from pyoaev._version import (  # noqa: F401
    __author__,
    __copyright__,
    __email__,
    __license__,
    __title__,
)
from pyoaev.asset_types import (  # noqa: F401
    AssetCategory,
    AssetCriticality,
    AssetSubCategory,
    CloudProvider,
)
from pyoaev.client import OpenAEV  # noqa: F401
from pyoaev.exceptions import *  # noqa: F401,F403,F405
from pyoaev.signatures import *  # noqa: F401,F403,F405

from typing_extensions import deprecated as _deprecated
from xtm_oaev_sdk import (
    BaseConfigModel as _BaseConfigModel,
    Configuration as _Configuration,
    ConfigLoaderCollector as _ConfigLoaderCollector,
    ConfigLoaderOAEV as _ConfigLoaderOAEV,
    ContractBuilder as _ContractBuilder,
    SettingsLoader as _SettingsLoader,
)

BaseConfigModel = _deprecated("Use 'from xtm_oaev_sdk import BaseConfigModel' instead.", category=DeprecationWarning)(_BaseConfigModel)
Configuration = _deprecated("Use 'from xtm_oaev_sdk import Configuration' instead.", category=DeprecationWarning)(_Configuration)
ConfigLoaderCollector = _deprecated("Use 'from xtm_oaev_sdk import ConfigLoaderCollector' instead.", category=DeprecationWarning)(_ConfigLoaderCollector)
ConfigLoaderOAEV = _deprecated("Use 'from xtm_oaev_sdk import ConfigLoaderOAEV' instead.", category=DeprecationWarning)(_ConfigLoaderOAEV)
ContractBuilder = _deprecated("Use 'from xtm_oaev_sdk import ContractBuilder' instead.", category=DeprecationWarning)(_ContractBuilder)
SettingsLoader = _deprecated("Use 'from xtm_oaev_sdk import SettingsLoader' instead.", category=DeprecationWarning)(_SettingsLoader)

__all__ = [
    "__author__",
    "__copyright__",
    "__email__",
    "__license__",
    "__title__",
    "__version__",
    "OpenAEV",
    "AssetCategory",
    "AssetSubCategory",
    "CloudProvider",
    "AssetCriticality",
]
__all__.extend(exceptions.__all__)  # noqa: F405
