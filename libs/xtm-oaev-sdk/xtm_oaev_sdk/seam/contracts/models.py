"""Contract data contracts: field types, elements and contract definitions.

The contract model hierarchy injectors and collectors use to declare their
input fields, output types, expectations and template variables. Elements own
their invariants (derived ``type``, cardinality, predefined expectations).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

__all__ = [
    "ContractAiTarget",
    "ContractAsset",
    "ContractAssetGroup",
    "ContractAttachment",
    "ContractCardinality",
    "ContractCardinalityElement",
    "ContractCheckbox",
    "ContractConfig",
    "ContractData",
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


class CredentialType(str, Enum):
    """Credential reference types shared with the OpenAEV platform.

    The Python mirror of the OpenAEV backend credential-type enum used by
    credential secret references. Values must stay label-for-label in sync with
    the platform so contracts can declare credential references without any
    translation layer.
    """

    IDENTITY = "IDENTITY"
    CLOUD_AWS = "CLOUD_AWS"
    CLOUD_AZURE = "CLOUD_AZURE"
    CLOUD_GCP = "CLOUD_GCP"


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
    AiTarget: str = "ai-target"
    Payload: str = "payload"
    CredentialReference: str = "credential-reference"


class ContractFieldKey(str, Enum):
    """Predefined field keys for special contract fields."""

    Asset: str = "assets"
    AssetGroup: str = "asset_groups"
    CredentialReference: str = "credential_reference"


class ContractOutputType(str, Enum):
    """Available output types for contract result declarations."""

    Text: str = "text"
    ActionOutput: str = "action_output"
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
    File: str = "file"
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


class PrimitiveType(str, Enum):
    """Semantic type of a contract argument's value, independent of how the field
    renders in the UI (see ``ContractFieldType``). Mirrors the openaev platform's
    own ``PrimitiveType`` label-for-label so a contract pushed from here needs no
    translation on the other end.
    """

    AccountWithPasswordNotRequired: str = "account_with_password_not_required"
    ActionOutput: str = "action_output"
    AdminUsername: str = "admin_username"
    AsreproastableAccount: str = "asreproastable_account"
    AssetGroupId: str = "asset_group_id"
    AssetId: str = "asset_id"
    ComputerName: str = "computer_name"
    CVE: str = "cve"
    DelegationAccount: str = "delegation_account"
    Document: str = "document"
    Domain: str = "domain"
    FileName: str = "file_name"
    FilePath: str = "file_path"
    GroupName: str = "group_name"
    Hash: str = "hash"
    Host: str = "host"
    IPv4: str = "ipv4"
    IPv6: str = "ipv6"
    IpSubnet: str = "ip_subnet"
    KerberoastableAccount: str = "kerberoastable_account"
    Key: str = "key"
    Number: str = "number"
    Password: str = "password"
    Permissions: str = "permissions"
    Port: str = "port"
    Service: str = "service"
    Severity: str = "severity"
    ShareName: str = "share_name"
    SID: str = "sid"
    TargetedAsset: str = "targeted-asset"
    Text: str = "text"
    Username: str = "username"
    Value: str = "value"
    VulnerabilityName: str = "vulnerability_name"
    VulnerabilityStatus: str = "vulnerability_status"


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


class SecurityPlatformType(str, Enum):
    """Categories of security platform expected to fulfil a technical expectation.

    When an expectation declares one or more of these, the platform focuses the
    technical (DETECTION / PREVENTION / VULNERABILITY) result on collectors of
    those types only (instead of every connected security platform). An empty
    list means "any security platform".
    """

    EDR: str = "EDR"
    XDR: str = "XDR"
    SIEM: str = "SIEM"
    SOAR: str = "SOAR"
    NDR: str = "NDR"
    ISPM: str = "ISPM"
    LLM_FIREWALL: str = "LLM_FIREWALL"
    AI_GATEWAY: str = "AI_GATEWAY"


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
    expectation_is_predefined: bool = False
    expectation_is_multi_selectable: bool = False
    # Security platform types expected to fulfil this expectation. Empty = any
    # platform (unchanged behaviour). Typically set for technical expectations
    # (DETECTION / PREVENTION / VULNERABILITY), left empty for MANUAL ones.
    expectation_expected_security_platform_types: list[SecurityPlatformType] = field(
        default_factory=list
    )


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
    # The argument's chaining/semantic type (``PrimitiveType``) — matches the
    # platform's own ``argumentType`` label-for-label. ``None`` for fields with
    # no established type; the platform normalizes a missing value to ``Text``.
    argumentType: PrimitiveType | None = None

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
class ContractData:
    """Data of a complete contract definition for an injector or collector.

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
    variables: list[ContractVariable] = field(default_factory=list)
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
class ContractReferencedCredential(ContractElement):
    """Credential reference field, optionally restricted to one credential type."""

    key: str = field(default=ContractFieldKey.CredentialReference.value, init=False)
    label: str = "Select a credential reference"
    mandatory: bool = False
    credential_reference_type: Optional[CredentialType] = None
    multiple: bool = True

    @property
    def get_type(self) -> str:
        return ContractFieldType.CredentialReference.value


@dataclass
class ContractExpectations(ContractCardinalityElement):
    """Expectation selection field with predefined options.

    ``availableExpectations`` is the full set the user may pick from;
    ``predefinedExpectations`` is the subset pre-filled by default. When
    ``predefinedExpectations`` is not provided explicitly it is derived from
    the available expectations flagged ``expectation_is_predefined=True``.
    """

    cardinality: str = ContractCardinality.Multiple
    # Full set the user may choose from in the "add expectation" picker.
    availableExpectations: list[Expectation] = field(default_factory=list)
    # Subset pre-filled by default. ``None`` means "not provided": the list is
    # then derived from the available expectations flagged predefined.
    predefinedExpectations: list[Expectation] | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.predefinedExpectations is None:
            self.predefinedExpectations = [
                expectation
                for expectation in self.availableExpectations
                if expectation.expectation_is_predefined
            ]

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
class ContractAiTarget(ContractCardinalityElement):
    """Selector for a pre-configured AiTarget asset (LLM endpoint / AI agent under test).

    Renders in the UI as an entity autocomplete (backed by the platform ``/ai_targets``
    options endpoint), analogous to the asset / asset group pickers. The selected value is
    the AI target's ``asset_id`` (AI targets are AI_TARGET-category assets), resolved by the
    executing injector at run time. Unlike ``ContractAsset`` the key is free-form so a
    contract can name the field as it wishes.
    """

    @property
    def get_type(self) -> str:
        return ContractFieldType.AiTarget.value


@dataclass
class ContractPayload(ContractCardinalityElement):
    """Payload selection field."""

    @property
    def get_type(self) -> str:
        return ContractFieldType.Payload.value
