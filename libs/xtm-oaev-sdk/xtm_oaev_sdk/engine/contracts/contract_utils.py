"""Contract utility types: cardinality and variable definitions.

Provides foundational types used by the contract building system
for defining field cardinality and template variables.
"""

from dataclasses import dataclass, field
from enum import Enum

__all__ = [
    "ContractCardinality",
    "ContractVariable",
    "VariableType",
]


class ContractCardinality(str, Enum):
    """Field cardinality in a contract definition.

    Attributes:
        One: Single value expected.
        Multiple: Multiple values (list) expected.
    """

    One: str = "1"
    Multiple: str = "n"


class VariableType(str, Enum):
    """Variable type classification for contract template variables.

    Attributes:
        String: Simple string value.
        Object: Nested object with children.
    """

    String: str = "String"
    Object: str = "Object"


@dataclass
class ContractVariable:
    """A template variable available for injection into contract fields.

    Args:
        key: Variable identifier (dot-notation for nested, e.g. "user.email").
        label: Human-readable description of the variable.
        type: Variable type (String or Object).
        cardinality: Whether this variable holds one or many values.
        children: Nested child variables (for Object type).
    """

    key: str
    label: str
    type: VariableType
    cardinality: ContractCardinality
    children: list["ContractVariable"] = field(default_factory=list)
