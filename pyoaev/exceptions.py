"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every name below resolves to the *identical*
xtm_oaev_sdk object and emits a :class:`DeprecationWarning` on access.
"""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

# Unchanged public export list of the legacy module (also extended into
# ``pyoaev.__all__``); ``OpenAEVError`` and ``on_http_error`` were reachable
# but never exported.
__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "ConfigurationError",
    "OpenAEVAuthenticationError",
    "OpenAEVHttpError",
    "OpenAEVParsingError",
    "RedirectError",
    "OpenAEVHeadError",
    "OpenAEVListError",
    "OpenAEVGetError",
    "OpenAEVUpdateError",
    "OpenAEVCreateError",
    "OpenAEVDeleteError",
    "SignatureTransmissionError",
]

_MOVED = [*__all__, "OpenAEVError", "on_http_error"]

_deprecated_getattr = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in _MOVED
    },
    module_name=__name__,
)


def __getattr__(name: str):  # PEP 562
    return _deprecated_getattr(name)
