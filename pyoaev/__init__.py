# -*- coding: utf-8 -*-
__version__ = "3.261021.0"

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from pyoaev import (  # noqa: F401
    asset_types,
    configuration,
    contracts,
    exceptions,
    signatures,
)
from pyoaev._version import (  # noqa: F401
    __author__,
    __copyright__,
    __email__,
    __license__,
    __title__,
)
from pyoaev.client import OpenAEV  # noqa: F401

__all__ = [  # moved names are served by the PEP 562 __getattr__ below
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
__all__.extend(exceptions.__all__)

# Names moved to xtm_oaev_sdk: served lazily (PEP 562) so that `import pyoaev`
# stays silent and only legacy access to a moved name warns.
__getattr__ = _make_deprecated_getattr(
    {
        **{
            name: (
                f"Use 'from xtm_oaev_sdk import {name}' instead.",
                getattr(_sdk, name),
            )
            for name in (
                *asset_types.__all__,
                *configuration.__all__,
                *contracts.__all__,
                *exceptions.__all__,
            )
        },
        **signatures._DEPRECATED,
    },
    module_name=__name__,
)
