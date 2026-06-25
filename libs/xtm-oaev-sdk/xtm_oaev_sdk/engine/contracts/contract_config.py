"""Contract configuration: field types, elements, and contract definitions.

Defines the full contract model hierarchy used by injectors and collectors
to declare their configuration schemas, input fields, and output types.

Key types:
    - ContractElement (ABC): Base for all contract field types.
    - Contract: A complete contract definition with fields, outputs, and metadata.
    - ContractExpectationType: Expectation classification for contract fields.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from xtm_oaev_sdk.engine.contracts.contract_utils import ContractCardinality, ContractVariable
from xtm_oaev_sdk.engine.contracts.variable_helper import VariableHelper
from xtm_oaev_sdk.engine.utils import EnhancedJSONEncoder

__all__ = [
    "Contract",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAttachment",
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
    "ContractSelect",
    "ContractTeam",
    "ContractText",
    "ContractTextArea",
    "ContractTuple",
    "Domain",
    "Expectation",
    "LinkedFieldModel",
    "SupportedLanguage",
    "prepare_contracts",
]


class SupportedLanguage(str, Enum):
    """Supported languages for contract label localization."""

    fr: str = "fr"
    en: str = "en"


class ContractFieldType(str, Enum):
    """Available field types for contract input definitions."""

    Text: str = "text"
    Number: str = "number"
    Tuple: str = "tuple"
    Checkbox: str = "checkbox"
    Textarea: str = "textarea"
    Select: str = "select"
    Article: str = "article"
    Challenge: str = "challenge"
    DependencySelect: str = "dependency-select"
    Attachment: str = "attachment"
    Team: str = "team"
    Expectation: str = "expectation"
    Asset: str = "asset"
    AssetGroup: str = "asset-group"
    Payload: str = "payload"


class ContractFieldKey(str, Enum):
    """Predefined field keys for special contract fields."""

    Asset: str = "assets"
    AssetGroup: str = "asset_groups"


class ContractOutputType(str, Enum):
    """Available output types for contract result declarations."""

    Text: str = "text"
    Number: str = "number"
    Port: str = "port"
    PortsScan: str = "portscan"
    IPv4: str = "ipv4"
    IPv6: str = "ipv6"
    CVE: str = "cve"
    Asset: str = "asset"
    Credentials: str = "credentials"
    Username: str = "username"
    Share: str = "share"
    AdminUsername: str = "admin_username"
    Group: str = "group"
    Computer: str = "computer"
    PasswordPolicy: str = "password_policy"
    Delegation: str = "delegation"
    Sid: str = "sid"
    Vulnerability: str = "vulnerability"
    AccountWithPasswordNotRequired: str = "account_with_password_not_required"
    ExpectationSignature: str = "expectation_signature"
    AsreproastableAccount: str = "asreproastable_account"
    KerberoastableAccount: str = "kerberoastable_account"


class ContractExpectationType(str, Enum):
    """Expectation type classification for contract fields.

    Defines the 8 expectation categories available in contract definitions.
    Renamed from ExpectationType to avoid collision with signatures module.
    """

    text: str = "TEXT"
    document: str = "DOCUMENT"
    article: str = "ARTICLE"
    challenge: str = "CHALLENGE"
    manual: str = "MANUAL"
    prevention: str = "PREVENTION"
    detection: str = "DETECTION"
    vulnerability: str = "VULNERABILITY"


@dataclass
class Expectation:
    """An expectation entry within a contract expectations field.

    Args:
        expectation_type: The category of expectation.
        expectation_name: Human-readable name.
        expectation_description: Detailed description.
        expectation_score: Score weight for this expectation.
        expectation_expectation_group: Whether this belongs to a group.
    """

    expectation_type: ContractExpectationType
    expectation_name: str
    expectation_description: str
    expectation_score: int
    expectation_expectation_group: bool


@dataclass
class LinkedFieldModel:
    """A linked field reference within a contract element."""

    key: str
    type: ContractFieldType


@dataclass
class ContractElement(ABC):
    """Abstract base for all contract field elements.

    Subclass this to define new field types. Each subclass must
    implement the ``get_type`` property returning the field type string.

    Args:
        key: Unique field identifier.
        label: Human-readable field label.
        mandatory: Whether this field is required.
        readOnly: Whether this field is read-only in the UI.
    """

    key: str
    label: str
    type: str = field(default="", init=False)
    mandatoryGroups: list[str] = field(default_factory=list)
    mandatoryConditionFields: list[str] = field(default_factory=list)
    mandatoryConditionValues: dict[str, Any] = field(default_factory=list)
    visibleConditionFields: list[str] = field(default_factory=list)
    visibleConditionValues: dict[str, Any] = field(default_factory=list)
    linkedFields: list[str] = field(default_factory=list)
    mandatory: bool = False
    readOnly: bool = False

    @property
    @abstractmethod
    def get_type(self) -> str:
        """Return the contract field type string."""
        pass

    def __post_init__(self) -> None:
        self.type = self.get_type


@dataclass
class ContractCardinalityElement(ContractElement, ABC):
    """Contract element with cardinality (single vs multiple values)."""

    cardinality: str = ContractCardinality.One
    defaultValue: list[str] = field(default_factory=list)


@dataclass
class ContractOutputElement(ABC):
    """An output field declaration in a contract.

    Args:
        type: Output type (from ContractOutputType).
        field: Field identifier.
        labels: Localized labels for the output.
        isFindingCompatible: Whether output maps to a finding.
        isMultiple: Whether multiple values are produced.
    """

    type: str
    field: str
    labels: list[str]
    isFindingCompatible: bool
    isMultiple: bool


@dataclass
class ContractConfig:
    """Contract display configuration.

    Args:
        type: Contract type identifier.
        expose: Whether this contract is visible in the UI.
        label: Localized labels.
        color_dark: Hex color for dark theme.
        color_light: Hex color for light theme.
    """

    type: str
    expose: bool
    label: dict[SupportedLanguage, str]
    color_dark: str
    color_light: str


@dataclass
class Domain:
    """A domain classification for a contract."""

    domain_id: str
    domain_name: str
    domain_color: str
    domain_created_at: str
    domain_updated_at: str


@dataclass
class Contract:
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

    contract_id: str
    label: dict[SupportedLanguage, str]
    fields: list[ContractElement]
    outputs: list[ContractOutputElement]
    config: ContractConfig
    manual: bool
    variables: list[ContractVariable] = field(
        default_factory=lambda: (
            [
                VariableHelper.user_variable(),
                VariableHelper.exercise_variable(),
                VariableHelper.team_variable(),
            ]
            + VariableHelper.uri_variables()
        )
    )
    contract_attack_patterns_external_ids: list[str] = field(default_factory=list)
    contract_vulnerability_external_ids: list[str] = field(default_factory=list)
    is_atomic_testing: bool = True
    platforms: list[str] = field(default_factory=list)
    external_id: str | None = None
    domains: list[Domain] | None = None

    def add_attack_pattern(self, var: str) -> None:
        """Append an attack pattern external ID to this contract."""
        self.contract_attack_patterns_external_ids.append(var)

    def add_vulnerability(self, var: str) -> None:
        """Append a vulnerability external ID to this contract."""
        self.contract_vulnerability_external_ids.append(var)

    def add_variable(self, var: ContractVariable) -> None:
        """Add a custom template variable to this contract."""
        self.variables.append(var)

    def to_contract_add_input(self, source_id: str) -> dict[str, Any]:
        """Serialize this contract for the platform creation API.

        Args:
            source_id: The injector ID that owns this contract.

        Returns:
            Dict payload for the contract creation endpoint.
        """
        return {
            "contract_id": self.contract_id,
            "external_contract_id": self.external_id,
            "injector_id": source_id,
            "contract_manual": self.manual,
            "contract_labels": self.label,
            "contract_attack_patterns_external_ids": self.contract_attack_patterns_external_ids,
            "contract_vulnerability_external_ids": self.contract_vulnerability_external_ids,
            "contract_content": json.dumps(self, cls=EnhancedJSONEncoder),
            "is_atomic_testing": self.is_atomic_testing,
            "contract_platforms": self.platforms,
            "contract_domains": self.domains,
        }

    def to_contract_update_input(self) -> dict[str, Any]:
        """Serialize this contract for the platform update API.

        Returns:
            Dict payload for the contract update endpoint.
        """
        return {
            "contract_manual": self.manual,
            "contract_labels": self.label,
            "contract_attack_patterns_external_ids": self.contract_attack_patterns_external_ids,
            "contract_vulnerability_external_ids": self.contract_vulnerability_external_ids,
            "contract_content": json.dumps(self, cls=EnhancedJSONEncoder),
            "is_atomic_testing": self.is_atomic_testing,
            "contract_platforms": self.platforms,
            "contract_domains": self.domains,
        }


@dataclass
class ContractTeam(ContractCardinalityElement):
    """Team selection field."""

    @property
    def get_type(self) -> str:
        return ContractFieldType.Team.value


@dataclass
class ContractText(ContractCardinalityElement):
    """Text input field with optional default value."""

    defaultValue: str = ""

    @property
    def get_type(self) -> str:
        return ContractFieldType.Text.value


def prepare_contracts(contracts: list[Contract]) -> list[dict[str, Any]]:
    """Serialize a list of contracts for bulk platform registration.

    Args:
        contracts: List of Contract instances to serialize.

    Returns:
        List of dicts suitable for the bulk contract registration API.
    """
    return list(
        map(
            lambda c: {
                "contract_id": c.contract_id,
                "contract_labels": c.label,
                "contract_attack_patterns_external_ids": c.contract_attack_patterns_external_ids,
                "contract_content": json.dumps(c, cls=EnhancedJSONEncoder),
                "contract_platforms": c.platforms,
                "contract_domains": c.domains,
            },
            contracts,
        )
    )


@dataclass
class ContractTuple(ContractCardinalityElement):
    """Tuple (multi-value) input field with optional file attachment."""

    def __post_init__(self) -> None:
        super().__post_init__()
        self.cardinality = ContractCardinality.Multiple

    attachmentKey: str | None = None
    contractAttachment: bool = False
    tupleFilePrefix: str = "file :: "

    @property
    def get_type(self) -> str:
        return ContractFieldType.Tuple.value


@dataclass
class ContractTextArea(ContractCardinalityElement):
    """Textarea input field with optional rich text support."""

    defaultValue: str = ""
    richText: bool = False

    @property
    def get_type(self) -> str:
        return ContractFieldType.Textarea.value


@dataclass
class ContractCheckbox(ContractElement):
    """Checkbox (boolean) input field."""

    defaultValue: bool = False

    @property
    def get_type(self) -> str:
        return ContractFieldType.Checkbox.value


@dataclass
class ContractAttachment(ContractCardinalityElement):
    """File attachment field."""

    @property
    def get_type(self) -> str:
        return ContractFieldType.Attachment.value


@dataclass
class ContractExpectations(ContractCardinalityElement):
    """Expectation selection field with predefined options."""

    cardinality = ContractCardinality.Multiple
    predefinedExpectations: list[Expectation] = field(default_factory=list)

    @property
    def get_type(self) -> str:
        return ContractFieldType.Expectation.value


@dataclass
class ContractSelect(ContractCardinalityElement):
    """Dropdown select field with predefined choices."""

    choices: dict[str, str] | None = None

    @property
    def get_type(self) -> str:
        return ContractFieldType.Select.value


@dataclass
class ContractAsset(ContractCardinalityElement):
    """Asset selection field (key auto-set to 'assets')."""

    key: str = field(default=ContractFieldKey.Asset.value, init=False)

    @property
    def get_type(self) -> str:
        return ContractFieldType.Asset.value


@dataclass
class ContractAssetGroup(ContractCardinalityElement):
    """Asset group selection field (key auto-set to 'asset_groups')."""

    key: str = field(default=ContractFieldKey.AssetGroup.value, init=False)

    @property
    def get_type(self) -> str:
        return ContractFieldType.AssetGroup.value


@dataclass
class ContractPayload(ContractCardinalityElement):
    """Payload selection field."""

    @property
    def get_type(self) -> str:
        return ContractFieldType.Payload.value
