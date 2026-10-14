"""DEPRECATED: the daemon runtime moved to :mod:`xtm_oaev_sdk` and
:mod:`collectors_sdk`; the legacy names keep building the OpenAEV client."""

from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from .base_daemon import _ClientBaseDaemon
from .collector_daemon import _COLLECTOR_DAEMON_MESSAGE, _ClientCollectorDaemon

__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "BaseDaemon",
    "CollectorDaemon",
]

__getattr__ = _make_deprecated_getattr(
    {
        "BaseDaemon": (
            "Use 'from xtm_oaev_sdk import BaseDaemon' and pass "
            "api_client=OpenAEV(...) instead.",
            _ClientBaseDaemon,
        ),
        "CollectorDaemon": (_COLLECTOR_DAEMON_MESSAGE, _ClientCollectorDaemon),
    },
    module_name=__name__,
)
