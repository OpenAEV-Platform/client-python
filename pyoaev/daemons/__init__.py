from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from .base_daemon import _ClientBaseDaemon
from .collector_daemon import CollectorDaemon

__all__ = ["BaseDaemon", "CollectorDaemon"]

__getattr__ = _make_deprecated_getattr(
    {
        "BaseDaemon": (
            "Use 'from xtm_oaev_sdk import BaseDaemon' and pass "
            "api_client=OpenAEV(...) instead.",
            _ClientBaseDaemon,
        ),
    },
    module_name=__name__,
)
