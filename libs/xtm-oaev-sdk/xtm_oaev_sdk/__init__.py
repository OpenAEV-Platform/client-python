"""xtm-oaev-sdk — OpenAEV SDK core (DDD + Light Hex Architecture).

Architecture:
    _core/                Shared implementations (errors, utils, ssl_utils,
                          asset_types, security_domain)
    _core/configuration/  Configuration feature implementation
    _core/signatures/     Signature feature implementation
    seam/common/          Shared errors, enums, types, and utilities
    seam/configuration/   Configuration I/O surface
    seam/signatures/      Signatures inbound I/O seam (versioned)
    seam/port_io/         Port I/O wire schema (versioned, seam-owned)
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
