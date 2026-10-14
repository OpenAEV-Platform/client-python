"""PEP 562 module deprecation — a reusable compatibility primitive.

This is the mechanism behind *"this name moved / was renamed / is going
away, here's the new home."*

A module that wants to retire one or more names without breaking existing
consumers declares a mapping from each old name to
``(deprecation_message, replacement)`` and installs a module-level
``__getattr__`` built by :func:`make_deprecated_getattr`::

    from xtm_oaev_sdk.seam.deprecation import make_deprecated_getattr

    _DEPRECATED: dict[str, tuple[str, object]] = {
        "OldName": ("Use 'from xtm_oaev_sdk import NewName' instead.", NewName),
    }

    def __getattr__(name: str):  # PEP 562
        return make_deprecated_getattr(_DEPRECATED, module_name=__name__)(name)

Why a factory, and why it returns the object directly:

- **One primitive, many modules.** The ``__getattr__`` body is otherwise
  copy-pasted across a dozen legacy modules. A factory turns each copy into
  a data-driven mapping, so the warn / return / raise logic lives in a single
  tested place and every module only supplies the names it retires.
- **Identity is preserved.** The factory returns *exactly* the object the new
  name refers to — the same object, not a wrapper. No ``__new__`` / ``__call__``
  interception, no PEP 702 class. Wrappers deliberately mutate ``__new__`` and
  add indirection that breaks ``isinstance`` checks, metaclass handling, and
  signature introspection, so they are *not* used here.
- **Real misses still fail.** A name that is not in the mapping raises
  ``AttributeError`` (naming the module), so a typo or a not-yet-retired name
  is never silently swallowed by the deprecation layer.

This module is a *pure compatibility primitive*: it imports nothing from the
SDK's capabilities, so the dependency direction of the seam holds — the seam
is imported by consumers, never the other way round.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping as _Mapping
from typing import Any

__all__ = ["make_deprecated_getattr"]


def make_deprecated_getattr(
    mapping: _Mapping[str, tuple[str, Any]],
    *,
    module_name: str | None = None,
):
    """Build a PEP 562 module-level ``__getattr__`` for a set of deprecated names.

    Parameters
    ----------
    mapping:
        ``{old_name: (deprecation_message, replacement)}``. On first access to
        ``old_name`` the ``deprecation_message`` is emitted as a
        ``DeprecationWarning`` (``stacklevel=2``) and the ``replacement`` object
        is returned.
    module_name:
        Optional dotted name used in the ``AttributeError`` for a name that is
        *not* in ``mapping`` (e.g. ``"pyoaev.helpers"``). Defaults to
        ``"this module"``.

    Returns
    -------
    A zero-argument-per-call ``__getattr__(name)`` callable, suitable for
    assignment as a module's ``__getattr__``.

    Notes
    -----
    The input mapping is validated once and copied, so later mutation of the
    caller's mapping does not affect the returned callable. A malformed entry
    (non-string key, or a value that is not a two-item ``(message, target)``)
    raises ``ValueError`` at call time — i.e. at import time of the module that
    installs the shim — rather than at first access.
    """
    resolved: dict[str, tuple[str, Any]] = {}
    for key, value in mapping.items():
        if not isinstance(key, str) or not key:
            raise ValueError(
                f"deprecated-name mapping keys must be non-empty strings, got {key!r}"
            )
        if not isinstance(value, tuple) or len(value) != 2:
            raise ValueError(
                f"mapping entry for {key!r} must be (message, target), got {value!r}"
            )
        resolved[key] = (value[0], value[1])

    def __getattr__(name: str) -> Any:
        entry = resolved.get(name)
        if entry is None:
            where = module_name if module_name is not None else "this module"
            raise AttributeError(f"{where} has no attribute {name!r}") from None
        message, target = entry
        warnings.warn(message, DeprecationWarning, stacklevel=2)
        return target

    return __getattr__
