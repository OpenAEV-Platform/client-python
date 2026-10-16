"""Contract adapters: contract definitions, field builder, template variables.

Each adapter speaks the contracts seam types and delegates to the core
implementation of its port.

Example:
    >>> builder = ContractBuilder()
    >>> builder.mandatory(ContractText(key="name", label="Name"))
    >>> builder.optional(ContractCheckbox(key="verbose", label="Verbose"))
    >>> fields = builder.build_fields()
"""

from dataclasses import dataclass, field
from typing import Any

from xtm_oaev_sdk._core.contracts import (
    BuiltinContractVariables,
    ContractAssembly,
    ContractSerializer,
    CredentialReferences,
)
from xtm_oaev_sdk.seam.contracts import (
    ContractAiTarget,
    ContractAssemblyPort,
    ContractAsset,
    ContractAssetGroup,
    ContractAttachment,
    ContractBuilderProtocol,
    ContractCardinality,
    ContractCardinalityElement,
    ContractCheckbox,
    ContractConfig,
    ContractCredentialsPort,
    ContractData,
    ContractElement,
    ContractExpectations,
    ContractExpectationType,
    ContractFieldKey,
    ContractFieldType,
    ContractOutputElement,
    ContractOutputType,
    ContractPayload,
    ContractReferencedCredential,
    ContractSelect,
    ContractSerializerPort,
    ContractTeam,
    ContractText,
    ContractTextArea,
    ContractTuple,
    ContractVariable,
    ContractVariablesPort,
    CredentialType,
    Domain,
    Expectation,
    LinkedFieldModel,
    PrimitiveType,
    SecurityPlatformType,
    SupportedLanguage,
    VariableType,
)

__all__ = [
    "Contract",
    "ContractAiTarget",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAttachment",
    "ContractBuilder",
    "ContractBuilderProtocol",
    "ContractCardinality",
    "ContractCardinalityElement",
    "ContractCheckbox",
    "ContractConfig",
    "ContractElement",
    "ContractExpectationType",
    "ContractExpectations",
    "ContractFieldKey",
    "ContractFieldType",
    "ContractOutputElement",
    "ContractOutputType",
    "ContractPayload",
    "ContractReferencedCredential",
    "ContractSelect",
    "ContractTeam",
    "ContractText",
    "ContractTextArea",
    "ContractTuple",
    "ContractVariable",
    "CredentialType",
    "Domain",
    "Expectation",
    "LinkedFieldModel",
    "PrimitiveType",
    "SecurityPlatformType",
    "SupportedLanguage",
    "VariableHelper",
    "VariableType",
    "build_single_referenced_credential_element",
    "prepare_contracts",
]

_assembly: ContractAssemblyPort = ContractAssembly()
_variables: ContractVariablesPort = BuiltinContractVariables()
_serializer: ContractSerializerPort = ContractSerializer()
_credentials: ContractCredentialsPort = CredentialReferences()


class VariableHelper:
    """Factory for standard contract template variables.

    Provides pre-built variable definitions for common injection
    targets (users, exercises, teams, platform URIs).

    Example:
        >>> variables = [
        ...     VariableHelper.user_variable(),
        ...     VariableHelper.exercise_variable(),
        ...     VariableHelper.team_variable(),
        ... ] + VariableHelper.uri_variables()
    """

    @staticmethod
    def user_variable() -> ContractVariable:
        """Create the user template variable with standard children."""
        return _variables.user_variable()

    @staticmethod
    def exercise_variable() -> ContractVariable:
        """Create the exercise template variable with standard children."""
        return _variables.exercise_variable()

    @staticmethod
    def team_variable() -> ContractVariable:
        """Create the teams template variable."""
        return _variables.team_variable()

    @staticmethod
    def uri_variables() -> list[ContractVariable]:
        """Create platform URI template variables."""
        return _variables.uri_variables()


@dataclass
class Contract(ContractData):
    """A complete contract definition for an injector or collector.

    Contains fields (inputs), outputs, configuration, and metadata
    for registering the contract with the OpenAEV platform.

    Args:
        contract_id: Unique contract identifier.
        label: Localized contract labels.
        fields: Input field definitions.
        outputs: Output field declarations.
        config: Display configuration.
        manual: Whether this is a manual-execution contract.
        variables: Template variables available for injection.
    """

    variables: list[ContractVariable] = field(
        default_factory=lambda: _variables.default_variables()
    )

    def to_contract_add_input(self, source_id: str) -> dict[str, Any]:
        """Serialize this contract for the platform creation API.

        Args:
            source_id: The injector ID that owns this contract.

        Returns:
            Dict payload for the contract creation endpoint.
        """
        return _serializer.to_add_input(self, source_id)

    def to_contract_update_input(self) -> dict[str, Any]:
        """Serialize this contract for the platform update API.

        Returns:
            Dict payload for the contract update endpoint.
        """
        return _serializer.to_update_input(self)


def prepare_contracts(contracts: list[Contract]) -> list[dict[str, Any]]:
    """Serialize a list of contracts for bulk platform registration.

    Args:
        contracts: List of Contract instances to serialize.

    Returns:
        List of dicts suitable for the bulk contract registration API.
    """
    return _serializer.prepare(contracts)


def build_single_referenced_credential_element(
    provider_name: str,
) -> ContractReferencedCredential:
    """Build a credential-reference field for a provider-specific contract
    with ``multiple`` value at ``False``.

    This is the centralized entry point injectors should use when they need the
    OpenAEV inject form to ask for one referenced credential. The helper keeps
    provider-to-``CredentialType`` mapping consistent across injector projects.
    """
    return _credentials.build_single_referenced_credential_element(provider_name)


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
        self.fields = _assembly.concat(self.fields, fields)
        return self

    def add_outputs(self, outputs: list[ContractOutputElement]) -> "ContractBuilder":
        """Add multiple output declarations at once.

        Args:
            outputs: List of output elements to add.

        Returns:
            Self for chaining.
        """
        self.outputs = _assembly.concat(self.outputs, outputs)
        return self

    def mandatory(self, element: ContractElement) -> "ContractBuilder":
        """Add a mandatory field.

        Args:
            element: The contract element to mark as mandatory.

        Returns:
            Self for chaining.
        """
        self.fields.append(_assembly.set_mandatory(element, True))
        return self

    def optional(self, element: ContractElement) -> "ContractBuilder":
        """Add an optional field.

        Args:
            element: The contract element to mark as optional.

        Returns:
            Self for chaining.
        """
        self.fields.append(_assembly.set_mandatory(element, False))
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
        self.fields.extend(_assembly.require_group(elements))
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
