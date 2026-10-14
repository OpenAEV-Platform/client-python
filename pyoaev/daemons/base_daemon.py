"""DEPRECATED: moved to :mod:`xtm_oaev_sdk`.

The SDK ``BaseDaemon`` takes an injected API client. The legacy name resolves
to a thin subclass that keeps building the ``OpenAEV`` client from the
``openaev_url``, ``openaev_token`` and ``openaev_tenant_id`` configuration
keys when none is passed, and emits a :class:`DeprecationWarning` on access.
"""

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

from pyoaev.client import OpenAEV


class _ClientBaseDaemon(_sdk.BaseDaemon):
    """SDK BaseDaemon building an OpenAEV client when none is injected."""

    def _create_default_api_client(self) -> OpenAEV:
        return OpenAEV(
            url=self._configuration.get("openaev_url"),
            token=self._configuration.get("openaev_token"),
            tenant_id=self._configuration.get("openaev_tenant_id"),
        )


__all__ = ["BaseDaemon"]  # noqa: F822 (served by the PEP 562 __getattr__ below)

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
