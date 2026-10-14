"""The architectural **seam** — the versioned compatibility boundary.

Everything in this layer pins a stable interface so that the two sides of it
can evolve independently without leaking either:

- **``common``** — the shared vocabulary (errors, enums, value objects,
  consumer protocols) and the common ports; closed and versioned
  (``SEAM_VERSION``).
- **``configuration``** — the configuration contracts (hints, settings
  models, serialization types) and the ports its public adapters delegate
  to; closed and versioned (``SEAM_VERSION``).
- **``contracts``** — the OpenAEV scenario data contracts (contract
  definitions, field elements, enums, template variables), the builder
  protocol and the ports its public adapters delegate to; closed and
  versioned (``SEAM_VERSION``).
- **``daemons``** — the ports of the daemon runtime shared by collectors and
  injectors (lifecycle, heartbeat); closed and versioned (``SEAM_VERSION``).
- **``signatures``** — the matching vocabulary and policies, the signature
  ports, and the inbound I/O models (``seam/signatures/seam.py``, versioned
  ``SEAM_VERSION``).
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

``common``, ``configuration``, ``contracts``, ``daemons``, ``signatures`` and
``port_io`` are closed; only ``deprecation`` remains to be layered.
"""

from xtm_oaev_sdk.seam.deprecation import make_deprecated_getattr

__all__ = ["make_deprecated_getattr"]
