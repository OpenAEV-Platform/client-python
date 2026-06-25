"""Contract builder: fluent API for constructing contract field sets.

Provides the ContractBuilder class and its Protocol for building
contract input field and output declarations with a chainable API.

Example:
    >>> builder = ContractBuilder()
    >>> builder.mandatory(ContractText(key="name", label="Name"))
    >>> builder.optional(ContractCheckbox(key="verbose", label="Verbose"))
    >>> fields = builder.build_fields()
"""

from typing import Protocol, runtime_checkable

from xtm_oaev_sdk._core.contracts.contract_config import (
    ContractElement,
    ContractOutputElement,
)

__all__ = [
    "ContractBuilder",
    "ContractBuilderProtocol",
]


@runtime_checkable
class ContractBuilderProtocol(Protocol):
    """Behavioral contract for contract field builders.

    Defines the chainable API for constructing contract field sets.
    Consumers can code against this protocol for testability.
    """

    def add_fields(self, fields: list[ContractElement]) -> "ContractBuilderProtocol":
        """Add multiple fields at once."""
        ...

    def add_outputs(self, outputs: list[ContractOutputElement]) -> "ContractBuilderProtocol":
        """Add multiple output declarations at once."""
        ...

    def mandatory(self, element: ContractElement) -> "ContractBuilderProtocol":
        """Add a mandatory field."""
        ...

    def optional(self, element: ContractElement) -> "ContractBuilderProtocol":
        """Add an optional field."""
        ...

    def mandatory_group(self, elements: list[ContractElement]) -> "ContractBuilderProtocol":
        """Add a group of mutually-required fields."""
        ...

    def build_fields(self) -> list[ContractElement]:
        """Return the accumulated fields."""
        ...

    def build_outputs(self) -> list[ContractOutputElement]:
        """Return the accumulated outputs."""
        ...


class ContractBuilder:
    """Fluent builder for contract field and output declarations.

    Provides a chainable API to construct contract definitions
    with mandatory, optional, and grouped fields.

    Example:
        >>> b = ContractBuilder()
        >>> b.mandatory(ContractText(key="target", label="Target URL"))
        >>> b.optional(ContractCheckbox(key="verify_ssl", label="Verify SSL"))
        >>> fields = b.build_fields()
        >>> len(fields)
        2
    """

    fields: list[ContractElement]
    outputs: list[ContractOutputElement]

    def __init__(self) -> None:
        self.fields = []
        self.outputs = []

    def add_fields(self, fields: list[ContractElement]) -> "ContractBuilder":
        """Add multiple fields at once.

        Args:
            fields: List of contract elements to add.

        Returns:
            Self for chaining.
        """
        self.fields = self.fields + fields
        return self

    def add_outputs(self, outputs: list[ContractOutputElement]) -> "ContractBuilder":
        """Add multiple output declarations at once.

        Args:
            outputs: List of output elements to add.

        Returns:
            Self for chaining.
        """
        self.outputs = self.outputs + outputs
        return self

    def mandatory(self, element: ContractElement) -> "ContractBuilder":
        """Add a mandatory field.

        Args:
            element: The contract element to mark as mandatory.

        Returns:
            Self for chaining.
        """
        element.mandatory = True
        self.fields.append(element)
        return self

    def optional(self, element: ContractElement) -> "ContractBuilder":
        """Add an optional field.

        Args:
            element: The contract element to mark as optional.

        Returns:
            Self for chaining.
        """
        element.mandatory = False
        self.fields.append(element)
        return self

    def mandatory_group(self, elements: list[ContractElement]) -> "ContractBuilder":
        """Add a group of mutually-required fields.

        All fields in the group reference each other's keys and are
        marked mandatory.

        Args:
            elements: List of contract elements forming the group.

        Returns:
            Self for chaining.
        """
        keys: list[str] = list(map(lambda iterable: iterable.key, elements))
        for element in elements:
            element.mandatory = True
            element.mandatoryGroups = keys
            self.fields.append(element)
        return self

    def build_fields(self) -> list[ContractElement]:
        """Return all accumulated contract fields.

        Returns:
            List of ContractElement instances added via this builder.
        """
        return self.fields

    def build_outputs(self) -> list[ContractOutputElement]:
        """Return all accumulated output declarations.

        Returns:
            List of ContractOutputElement instances added via this builder.
        """
        return self.outputs
