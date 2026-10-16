"""Deprecation shims: PEP 562 ``__getattr__`` serving retired names."""

import warnings
from collections.abc import Mapping
from typing import Any, Callable

__all__ = ["DeprecationShims"]


class DeprecationShims:
    """Implements ``DeprecationPort``."""

    def resolve_mapping(
        self, mapping: Mapping[str, tuple[str, Any]]
    ) -> dict[str, tuple[str, Any]]:
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
        return resolved

    def build_getattr(
        self, resolved: dict[str, tuple[str, Any]], module_name: str | None
    ) -> Callable[[str], Any]:
        def __getattr__(name: str) -> Any:
            entry = resolved.get(name)
            if entry is None:
                where = module_name if module_name is not None else "this module"
                raise AttributeError(f"{where} has no attribute {name!r}") from None
            message, target = entry
            warnings.warn(message, DeprecationWarning, stacklevel=2)
            return target

        return __getattr__
