"""JSON encoding of the objects the standard encoder does not support."""

import dataclasses
from typing import Any

__all__ = ["JsonEncoding"]


class JsonEncoding:
    """Implements ``JsonEncodingPort``."""

    def encode_default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        # same error as json.JSONEncoder.default
        raise TypeError(
            f"Object of type {o.__class__.__name__} is not JSON serializable"
        )
