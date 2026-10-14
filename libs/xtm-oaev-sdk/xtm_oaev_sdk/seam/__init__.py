"""The architectural **seam** — the versioned compatibility boundary.

Everything in this layer pins a stable interface so that the two sides of it
can evolve independently without leaking either:

- **``configuration``** — the configuration capability's I/O models and
  conversion primitives.
- **``deprecation``** — the PEP 562 deprecation primitive
  (:func:`make_deprecated_getattr`) for retiring public names without
  breaking importers.

The package ``__init__`` surfaces present ``_core``'s stable vocabulary
through the boundary: they import ``_core`` so the public layer can. The seam
is the **sole door** between ``public/`` and ``_core/``: every public import
of a ``_core`` symbol crosses it. The seam never imports the public layer,
nor does ``_core``.
"""

from xtm_oaev_sdk.seam.deprecation import make_deprecated_getattr

__all__ = ["make_deprecated_getattr"]
