"""The architectural **seam** — the versioned compatibility boundary.

Everything in this layer pins a stable interface so that the two sides of it
can evolve independently without leaking either:

- **``common``** — shared errors, enums, types, and utilities: the
  platform-facing vocabulary both sides import.
- **``configuration``** — the configuration contracts (hints, settings
  models, serialization types) and the ports its public adapters delegate
  to; closed and versioned (``SEAM_VERSION``).
- **``contracts``** — the scenarios capability's behaviour layer (builder,
  variable helper, preparation entry point) and its extension protocol.
- **``daemons``** — the daemon runtime shared by collectors and injectors;
  the API client is injected through the ``BaseClient`` protocol.
- **``signatures``** — the signatures capability's inbound seam
  (``seam/signatures/seam.py``), versioned ``SEAM_VERSION``.
- **``port_io``** — the port I/O wire schema crossing the SDK↔platform
  boundary; the seam **owns** the models (``seam/port_io/models.py``),
  versioned ``PORT_IO_CONTRACT_VERSION``.
- **``deprecation``** — the PEP 562 deprecation primitive
  (:func:`make_deprecated_getattr`) for retiring public names without
  breaking importers.

A seam is **closed**: it imports only the standard library, third-party data
libraries and sibling seam modules — never ``_core`` nor ``public``. The core
implements its ports; the public adapters speak its types and delegate to the
core. As long as the core keeps answering the seam, the public surface keeps
working; a seam change is a contract change (``SEAM_VERSION`` bump, changelog).

``configuration``, ``seam/signatures/seam.py`` and ``seam/port_io/models.py``
are closed today; the other packages still re-export ``_core`` until their
capability is migrated.

Distinct from the *business* :mod:`xtm_oaev_sdk.contracts` layer, which holds
the OpenAEV scenario data models — a domain concept, unrelated to the
boundary.
"""

from xtm_oaev_sdk.seam.deprecation import make_deprecated_getattr

__all__ = ["make_deprecated_getattr"]
