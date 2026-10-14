"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every name below resolves to the *identical*
xtm_oaev_sdk object and emits a :class:`DeprecationWarning` on access.
"""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "BaseConfigModel",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "HttpUrlToString",
    "LogLevelToLower",
    "SettingsLoader",
    "TimedeltaInSeconds",
]

_deprecated_getattr = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in __all__
    },
    module_name=__name__,
)


def __getattr__(name: str):  # PEP 562
    return _deprecated_getattr(name)
