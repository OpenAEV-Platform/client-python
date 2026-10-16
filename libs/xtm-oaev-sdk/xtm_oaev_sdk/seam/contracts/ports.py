"""Contract ports: the behaviour the public layer expects from the core.

``ContractBuilderProtocol`` is the consumer-facing contract of field builders.
The other protocols are the ports the public adapters delegate to; the core
implements them.
"""

from typing import Any, Protocol, runtime_checkable

from xtm_oaev_sdk.seam.contracts.models import (
    ContractData,
    ContractElement,
    ContractOutputElement,
    ContractReferencedCredential,
    ContractVariable,
)

__all__ = [
    "ContractAssemblyPort",
    "ContractBuilderProtocol",
    "ContractCredentialsPort",
    "ContractSerializerPort",
    "ContractVariablesPort",
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

    def add_outputs(
        self, outputs: list[ContractOutputElement]
    ) -> "ContractBuilderProtocol":
        """Add multiple output declarations at once."""
        ...

    def mandatory(self, element: ContractElement) -> "ContractBuilderProtocol":
        """Add a mandatory field."""
        ...

    def optional(self, element: ContractElement) -> "ContractBuilderProtocol":
        """Add an optional field."""
        ...

    def mandatory_group(
        self, elements: list[ContractElement]
    ) -> "ContractBuilderProtocol":
        """Add a group of mutually-required fields."""
        ...

    def build_fields(self) -> list[ContractElement]:
        """Return the accumulated fields."""
        ...

    def build_outputs(self) -> list[ContractOutputElement]:
        """Return the accumulated outputs."""
        ...


@runtime_checkable
class ContractAssemblyPort(Protocol):
    """Assembles the field and output lists of a contract."""

    def concat(self, existing: list[Any], extra: list[Any]) -> list[Any]:
        """New list made of ``existing`` followed by ``extra``."""

    def set_mandatory(
        self, element: ContractElement, mandatory: bool
    ) -> ContractElement:
        """The element, marked mandatory or optional."""

    def require_group(self, elements: list[ContractElement]) -> list[ContractElement]:
        """The elements, mandatory and referencing each other's keys."""


@runtime_checkable
class ContractVariablesPort(Protocol):
    """Provides the built-in contract template variables."""

    def user_variable(self) -> ContractVariable:
        """The user template variable with its standard children."""

    def exercise_variable(self) -> ContractVariable:
        """The exercise template variable with its standard children."""

    def team_variable(self) -> ContractVariable:
        """The teams template variable."""

    def uri_variables(self) -> list[ContractVariable]:
        """The platform URI template variables."""

    def default_variables(self) -> list[ContractVariable]:
        """The variables every contract starts with."""


@runtime_checkable
class ContractSerializerPort(Protocol):
    """Serializes contracts into platform API payloads."""

    def to_add_input(self, contract: ContractData, source_id: str) -> dict[str, Any]:
        """Payload of the contract creation endpoint."""

    def to_update_input(self, contract: ContractData) -> dict[str, Any]:
        """Payload of the contract update endpoint."""

    def prepare(self, contracts: list[ContractData]) -> list[dict[str, Any]]:
        """Payloads of the bulk contract registration endpoint."""


@runtime_checkable
class ContractCredentialsPort(Protocol):
    """Builds the credential-reference fields of a contract."""

    def build_single_referenced_credential_element(
        self, provider_name: str
    ) -> ContractReferencedCredential:
        """Credential-reference field asking for one credential of the provider's type."""
