"""xtm-oaev-sdk — OpenAEV SDK core (DDD + Light Hex Architecture).

Architecture:
    _core/                Shared implementations (errors, utils, ssl_utils, protocols,
                          asset_types, security_domain)
    _core/configuration/  Configuration feature implementation
    _core/contracts/      OpenAEV scenarios feature implementation
    _core/daemons/        Daemon runtime (base daemon, heartbeat)
    _core/signatures/     Signature feature implementation
    seam/common/          Shared errors, enums, types, and utilities
    seam/configuration/   Configuration contracts and ports (closed, versioned)
    seam/contracts/       Scenarios capability behaviour + builder protocol
    seam/daemons/         Daemon runtime (API client injected)
    seam/signatures/      Signatures inbound I/O seam (versioned)
    seam/port_io/         Port I/O wire schema (versioned, seam-owned)
    seam/deprecation.py   PEP 562 deprecation primitive
    contracts/contracts/  OpenAEV scenario data models (business layer)
    public/configuration  Configuration adapters
    public/               User-facing re-exports

Port/adapter layering, capability by capability (see ``seam``):

- ``seam`` holds the contracts — data models, enums, errors and the ``Protocol``
  ports — and imports nothing from ``_core`` nor ``public``;
- ``_core`` implements the seam ports and never imports ``public``;
- ``public`` exposes adapters that speak seam types and delegate to ``_core``,
  plus the seam contracts themselves — never a core object.

Capabilities not migrated yet still re-export ``_core`` through their seam
package.
"""

__version__ = "0.1.0"

from xtm_oaev_sdk.public import *  # noqa: F401, F403
from xtm_oaev_sdk.public import __all__ as _public_all

__all__ = list(_public_all)
