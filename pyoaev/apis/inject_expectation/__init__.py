import collectors_sdk as _collectors_sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from . import model  # noqa: F401  (legacy: exposed as pyoaev.apis.model)
from .inject_expectation import *  # noqa: F401,F403

# The expectation models moved to collectors_sdk; their legacy names here
# resolve to the identical objects and emit a DeprecationWarning on access.
__getattr__ = _make_deprecated_getattr(
    {
        name: (
            f"Use 'from collectors_sdk import {name}' instead.",
            getattr(_collectors_sdk, name),
        )
        for name in (
            "DetectionExpectation",
            "ExpectationTypeEnum",
            "PreventionExpectation",
        )
    },
    module_name=__name__,
)
