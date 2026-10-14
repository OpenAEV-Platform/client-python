"""PEP 562 module deprecation — a reusable compatibility primitive.

This is the mechanism behind *"this name moved / was renamed / is going
away, here's the new home."*

A module that wants to retire one or more names without breaking existing
consumers declares a mapping from each old name to
``(deprecation_message, replacement)`` and installs a module-level
``__getattr__`` built by :func:`make_deprecated_getattr`::

    from xtm_oaev_sdk import make_deprecated_getattr

    __getattr__ = make_deprecated_getattr(  # PEP 562
        {"OldName": ("Use 'from xtm_oaev_sdk import NewName' instead.", NewName)},
        module_name=__name__,
    )

Assign the factory's result directly: a ``def __getattr__`` wrapper adds a
frame, and the warning would then point at the shim instead of the caller.

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

This adapter speaks the deprecation seam types and delegates to the core
implementation of its port.
"""

from collections.abc import Mapping as _Mapping
from typing import Any

from xtm_oaev_sdk._core.deprecation import DeprecationShims
from xtm_oaev_sdk.seam.deprecation import DeprecationPort

__all__ = ["make_deprecated_getattr"]

_deprecation: DeprecationPort = DeprecationShims()


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
    return _deprecation.build_getattr(
        _deprecation.resolve_mapping(mapping), module_name
    )
