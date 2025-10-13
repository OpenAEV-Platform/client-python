import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from pyoaev import utils
from pyoaev.contracts.contract_utils import ContractCardinality, ContractVariable
from pyoaev.contracts.variable_helper import VariableHelper


class SupportedLanguage(str, Enum):
    fr: str = "fr"
    en: str = "en"


class ContractFieldType(str, Enum):
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
    Asset: str = "assets"
    AssetGroup: str = "asset_groups"

class ContractOutputType(str, Enum):
    Text: str = "text"
    Number: str = "number"
    Port: str = "port"
    PortsScan: str = "portscan"
    IPv4: str = "ipv4"
    IPv6: str = "ipv6"
    CVE: str = "cve"


class ExpectationType(str, Enum):
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
    expectation_type: ExpectationType
    expectation_name: str
    expectation_description: str
    expectation_score: int
    expectation_expectation_group: bool


@dataclass
class LinkedFieldModel:
    key: str
    type: ContractFieldType


@dataclass
class ContractElement(ABC):
    key: str
    label: str
    type: str = field(default="", init=False)
    mandatoryGroups: List[str] = field(default_factory=list)
    mandatoryConditionFields: List[str] = field(default_factory=list)
    mandatoryConditionValues: Dict[str, any] = field(default_factory=list)
    visibleConditionFields: List[str] = field(default_factory=list)
    visibleConditionValues: Dict[str, any] = field(default_factory=list)
    linkedFields: List[str] = field(default_factory=list)
    mandatory: bool = False
    readOnly: bool = False

    @property
    @abstractmethod
    def get_type(self) -> str:
        pass

    def __post_init__(self):
        self.type = self.get_type


@dataclass
class ContractCardinalityElement(ContractElement, ABC):
    cardinality: str = ContractCardinality.One
    defaultValue: List[str] = field(default_factory=list)


@dataclass
class ContractOutputElement(ABC):
    type: str
    field: str
    labels: List[str]
    isFindingCompatible: bool
    isMultiple: bool


@dataclass
class ContractConfig:
    type: str
    expose: bool
    label: dict[SupportedLanguage, str]
    color_dark: str
    color_light: str


@dataclass
class Contract:
    contract_id: str
    label: dict[SupportedLanguage, str]
    fields: List[ContractElement]
    outputs: List[ContractOutputElement]
    config: ContractConfig
    manual: bool
    variables: List[ContractVariable] = field(
        default_factory=lambda: [
            VariableHelper.user_variable(),
            VariableHelper.exercise_variable(),
            VariableHelper.team_variable(),
        ]
        + VariableHelper.uri_variables()
    )
    contract_attack_patterns_external_ids: List[str] = field(default_factory=list)
    contract_vulnerability_external_ids: List[str] = field(default_factory=list)
    is_atomic_testing: bool = True
    platforms: List[str] = field(default_factory=list)
    external_id: str = None

    def add_attack_pattern(self, var: str):
        self.contract_attack_patterns_external_ids.append(var)

    def add_vulnerability(self, var: str):
        self.contract_vulnerability_external_ids.append(var)

    def add_variable(self, var: ContractVariable):
        self.variables.append(var)

    def to_contract_add_input(self, source_id: str):
        return {
            "contract_id": self.contract_id,
            "external_contract_id": self.external_id,
            "injector_id": source_id,
            "contract_manual": self.manual,
            "contract_labels": self.label,
            "contract_attack_patterns_external_ids": self.contract_attack_patterns_external_ids,
            "contract_vulnerability_external_ids": self.contract_vulnerability_external_ids,
            "contract_content": json.dumps(self, cls=utils.EnhancedJSONEncoder),
            "is_atomic_testing": self.is_atomic_testing,
            "contract_platforms": self.platforms,
        }

    def to_contract_update_input(self):
        return {
            "contract_manual": self.manual,
            "contract_labels": self.label,
            "contract_attack_patterns_external_ids": self.contract_attack_patterns_external_ids,
            "contract_vulnerability_external_ids": self.contract_vulnerability_external_ids,
            "contract_content": json.dumps(self, cls=utils.EnhancedJSONEncoder),
            "is_atomic_testing": self.is_atomic_testing,
            "contract_platforms": self.platforms,
        }


@dataclass
class ContractTeam(ContractCardinalityElement):
    @property
    def get_type(self) -> str:
        return ContractFieldType.Team.value


@dataclass
class ContractText(ContractCardinalityElement):

    defaultValue: str = ""

    @property
    def get_type(self) -> str:
        return ContractFieldType.Text.value


def prepare_contracts(contracts):
    return list(
        map(
            lambda c: {
                "contract_id": c.contract_id,
                "contract_labels": c.label,
                "contract_attack_patterns_external_ids": c.contract_attack_patterns_external_ids,
                "contract_content": json.dumps(c, cls=utils.EnhancedJSONEncoder),
                "contract_platforms": c.platforms,
            },
            contracts,
        )
    )


@dataclass
class ContractTuple(ContractCardinalityElement):
    def __post_init__(self):
        super().__post_init__()
        self.cardinality = ContractCardinality.Multiple

    attachmentKey: str = None
    contractAttachment: bool = attachmentKey is not None
    tupleFilePrefix: str = "file :: "

    @property
    def get_type(self) -> str:
        return ContractFieldType.Tuple.value


@dataclass
class ContractTextArea(ContractCardinalityElement):

    defaultValue: str = ""
    richText: bool = False

    @property
    def get_type(self) -> str:
        return ContractFieldType.Textarea.value


@dataclass
class ContractCheckbox(ContractElement):

    defaultValue: bool = False

    @property
    def get_type(self) -> str:
        return ContractFieldType.Checkbox.value


@dataclass
class ContractAttachment(ContractCardinalityElement):

    @property
    def get_type(self) -> str:
        return ContractFieldType.Attachment.value


@dataclass
class ContractExpectations(ContractCardinalityElement):
    cardinality = ContractCardinality.Multiple
    predefinedExpectations: List[Expectation] = field(default_factory=list)

    @property
    def get_type(self) -> str:
        return ContractFieldType.Expectation.value


@dataclass
class ContractSelect(ContractCardinalityElement):

    choices: dict[str, str] = None

    @property
    def get_type(self) -> str:
        return ContractFieldType.Select.value


@dataclass
class ContractAsset(ContractCardinalityElement):
    key: str = field(default=ContractFieldKey.Asset.value, init=False)

    @property
    def get_type(self) -> str:
        return ContractFieldType.Asset.value

@dataclass
class ContractAssetGroup(ContractCardinalityElement):
    key: str = field(default=ContractFieldKey.AssetGroup.value, init=False)

    @property
    def get_type(self) -> str:
        return ContractFieldType.AssetGroup.value


@dataclass
class ContractPayload(ContractCardinalityElement):

    @property
    def get_type(self) -> str:
        return ContractFieldType.Payload.value
