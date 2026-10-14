"""Deprecation port: serve retired public names without breaking importers."""

from collections.abc import Mapping
from typing import Any, Callable, Protocol, runtime_checkable

__all__ = ["DeprecatedNames", "DeprecationPort"]

DeprecatedNames = Mapping[str, tuple[str, Any]]
"""``{old_name: (deprecation_message, replacement)}``."""


@runtime_checkable
class DeprecationPort(Protocol):
    """Builds PEP 562 module ``__getattr__`` functions for retired names."""

    def resolve_mapping(self, mapping: DeprecatedNames) -> dict[str, tuple[str, Any]]:
        """Validated copy of the mapping; ValueError on a malformed entry."""

    def build_getattr(
        self, resolved: dict[str, tuple[str, Any]], module_name: str | None
    ) -> Callable[[str], Any]:
        """``__getattr__`` warning (at the caller's line) and returning the
        replacement of a retired name, raising AttributeError otherwise."""
