"""xtm-oaev-sdk — OpenAEV SDK core (DDD + Light Hex Architecture).

Architecture:
    _core/common/         Common implementations (HTTP errors, logging, JSON
                          encoding, dict tools, certificates)
    _core/configuration/  Configuration feature implementation
    _core/contracts/      OpenAEV scenarios feature implementation
    _core/daemons/        Daemon runtime (base daemon, heartbeat)
    _core/deprecation/    Deprecation shims (PEP 562 __getattr__)
    _core/signatures/     Signature feature implementation
    seam/common/          Shared errors, enums, value objects, protocols, ports
    seam/configuration/   Configuration contracts and ports (closed, versioned)
    seam/contracts/       Scenario contracts and ports (closed, versioned)
    seam/daemons/         Daemon runtime ports (closed, versioned)
    seam/signatures/      Signature contracts, inbound I/O models and ports (closed)
    seam/port_io/         Port I/O wire schema (versioned, seam-owned)
    seam/deprecation/     Deprecation port (closed, versioned)
    public/common         Common adapters
    public/configuration  Configuration adapters
    public/contracts      Scenario contract adapters
    public/daemons        Daemon runtime adapters (API client injected)
    public/signatures     Signature manager and helpers adapters
    public/deprecation    PEP 562 deprecation primitive adapter
    public/               User-facing re-exports

Port/adapter layering, capability by capability (see ``seam``):

- ``seam`` holds the contracts — data models, enums, errors and the ``Protocol``
  ports — and imports nothing from ``_core`` nor ``public``;
- ``_core`` implements the seam ports and never imports ``public``;
- ``public`` exposes adapters that speak seam types and delegate to ``_core``,
  plus the seam contracts themselves — never a core object.

"""

__version__ = "0.1.0"

from xtm_oaev_sdk.public import *  # noqa: F401, F403
from xtm_oaev_sdk.public import __all__ as _public_all

__all__ = list(_public_all)
