"""DEPRECATED: moved to :mod:`collectors_sdk`.

Backward-compatibility shim: every name below resolves to the *identical*
collectors_sdk object and emits a :class:`DeprecationWarning` on access.
"""

import collectors_sdk as _collectors_sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "DetectionExpectation",
    "ExpectationTypeEnum",
    "PreventionExpectation",
]

__getattr__ = _make_deprecated_getattr(
    {
        name: (
            f"Use 'from collectors_sdk import {name}' instead.",
            getattr(_collectors_sdk, name),
        )
        for name in (*__all__, "Expectation", "ExpectationSignature")
    },
    module_name=__name__,
)
