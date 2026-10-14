"""The architectural **seam** — the versioned compatibility boundary.

Everything in this layer pins a stable interface so that the two sides of it
can evolve independently without leaking either:

- **``common``** — shared errors, enums, types, and utilities: the
  platform-facing vocabulary both sides import.
- **``configuration``** — the configuration capability's I/O models and
  conversion primitives.
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

``seam/signatures/seam.py`` and ``seam/port_io/models.py`` are closed: they
import only the standard library, pydantic, and sibling seam modules — never
``_core``. The capability's implementation imports and re-exports from them.

The other package ``__init__`` surfaces present ``_core``'s stable vocabulary
through the boundary: they import ``_core`` so the public layer can. The seam
is the **sole door** between ``public/`` and ``_core/``: every public import
of a ``_core`` symbol crosses it. The seam never imports the public layer,
nor does ``_core``.

Distinct from the *business* :mod:`xtm_oaev_sdk.contracts` layer, which holds
the OpenAEV scenario data models — a domain concept, unrelated to the
boundary.
"""

from xtm_oaev_sdk.seam.deprecation import make_deprecated_getattr

__all__ = ["make_deprecated_getattr"]
