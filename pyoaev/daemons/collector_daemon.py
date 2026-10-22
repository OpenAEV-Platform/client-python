"""DEPRECATED: moved to :mod:`collectors_sdk`.

The collectors-sdk ``CollectorDaemon`` takes an injected API client. The legacy
name resolves to a thin subclass that keeps building the ``OpenAEV`` client
from configuration when none is passed. Every other name resolves to the
*identical* SDK object. All names emit a :class:`DeprecationWarning` on access.
"""

import collectors_sdk as _collectors_sdk
import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from pyoaev.daemons.base_daemon import _ClientBaseDaemon


class _ClientCollectorDaemon(_collectors_sdk.CollectorDaemon, _ClientBaseDaemon):
    """collectors-sdk CollectorDaemon building an OpenAEV client when none is injected."""


_COLLECTOR_DAEMON_MESSAGE = (
    "Use 'from collectors_sdk import CollectorDaemon' and pass "
    "api_client=OpenAEV(...) instead."
)

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "CollectorDaemon",
    "DEFAULT_PERIOD_SECONDS",
    "DEFAULT_PLATFORM_TAG_COLOR",
]

__getattr__ = _make_deprecated_getattr(
    {
        "CollectorDaemon": (_COLLECTOR_DAEMON_MESSAGE, _ClientCollectorDaemon),
        "BaseDaemon": (
            "Use 'from xtm_oaev_sdk import BaseDaemon' and pass "
            "api_client=OpenAEV(...) instead.",
            _ClientBaseDaemon,
        ),
        **{
            name: (
                f"Use 'from collectors_sdk import {name}' instead.",
                getattr(_collectors_sdk, name),
            )
            for name in ("DEFAULT_PERIOD_SECONDS", "DEFAULT_PLATFORM_TAG_COLOR")
        },
        **{
            name: (
                f"Use 'from xtm_oaev_sdk import {name}' instead.",
                getattr(_sdk, name),
            )
            for name in ("Configuration", "PingAlive")
        },
    },
    module_name=__name__,
)
