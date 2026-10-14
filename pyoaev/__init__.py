# -*- coding: utf-8 -*-
__version__ = "3.261014.1"

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from pyoaev import configuration  # noqa: F401
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
from pyoaev.contracts import *  # noqa: F401,F403,F405
from pyoaev.exceptions import *  # noqa: F401,F403,F405
from pyoaev.signatures import *  # noqa: F401,F403,F405

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

# Names moved to xtm_oaev_sdk: served lazily (PEP 562) so that `import pyoaev`
# stays silent and only legacy access to a moved name warns.
_deprecated_getattr = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in configuration.__all__
    },
    module_name=__name__,
)


def __getattr__(name: str):  # PEP 562
    return _deprecated_getattr(name)
