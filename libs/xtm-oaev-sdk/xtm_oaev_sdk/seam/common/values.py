"""Value objects shared across capabilities: encoded identifiers and
field-presence rules."""

import dataclasses
import urllib.parse
from typing import Any

__all__ = ["EncodedId", "RequiredOptional"]


@dataclasses.dataclass(frozen=True)
class RequiredOptional:
    """Immutable field-presence validator for API payloads.

    Validates that required fields are present, optional fields are allowed,
    and exclusive fields follow mutual exclusion rules.

    Args:
        required: Tuple of field names that must be present.
        optional: Tuple of field names that may be present.
        exclusive: Tuple of field names where exactly one must be present.

    Example:
        >>> ro = RequiredOptional(required=("name", "type"), exclusive=("id", "key"))
        >>> ro.validate_attrs(data={"name": "x", "type": "y", "id": "123"})  # OK
        >>> ro.validate_attrs(data={"name": "x"})  # raises AttributeError
    """

    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    exclusive: tuple[str, ...] = ()

    def validate_attrs(
        self,
        *,
        data: dict[str, Any],
        excludes: list[str] | None = None,
    ) -> None:
        """Validate field presence against the configured rules.

        Args:
            data: Dict of field names to values to validate.
            excludes: Field names to skip during required-field checks.

        Raises:
            AttributeError: If required fields are missing, or exclusive
                field constraints are violated.
        """
        if excludes is None:
            excludes = []

        if self.required:
            required = [k for k in self.required if k not in excludes]
            missing = [attr for attr in required if attr not in data]
            if missing:
                raise AttributeError(f"Missing attributes: {', '.join(missing)}")

        if self.exclusive:
            exclusives = [attr for attr in data if attr in self.exclusive]
            if len(exclusives) > 1:
                raise AttributeError(
                    f"Provide only one of these attributes: {', '.join(exclusives)}"
                )
            if not exclusives:
                raise AttributeError(
                    f"Must provide one of these attributes: "
                    f"{', '.join(self.exclusive)}"
                )


class EncodedId(str):
    """URL-safe encoded identifier.

    Wraps a string or integer value with URL percent-encoding applied.
    Idempotent: encoding an already-encoded value returns it unchanged.

    Args:
        value: The raw identifier to encode. Accepts str, int, or EncodedId.

    Raises:
        TypeError: If value is not str, int, or EncodedId.

    Example:
        >>> EncodedId("hello world")
        'hello%20world'
        >>> EncodedId(42)
        '42'
    """

    def __new__(cls, value: "str | int | EncodedId") -> "EncodedId":
        if isinstance(value, EncodedId):
            return value

        if not isinstance(value, (int, str)):
            raise TypeError(f"Unsupported type received: {type(value)}")
        if isinstance(value, str):
            value = urllib.parse.quote(value, safe="")
        return super().__new__(cls, value)
