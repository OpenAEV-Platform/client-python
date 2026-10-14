"""xtm-oaev-sdk — OpenAEV SDK core (DDD + Light Hex Architecture).

Architecture:
    _core/configuration/  Configuration feature implementation
    seam/configuration/   Configuration I/O surface
    seam/deprecation.py   PEP 562 deprecation primitive
    public/               User-facing re-exports

The seam is the compatibility boundary and the sole door between the public
surface and ``_core``: the public layer reaches ``_core`` exclusively through
the seam, and nothing in ``_core`` imports ``public``.
"""

__version__ = "0.1.0"

from xtm_oaev_sdk.public import *  # noqa: F401, F403
from xtm_oaev_sdk.public import __all__ as _public_all

__all__ = list(_public_all)
