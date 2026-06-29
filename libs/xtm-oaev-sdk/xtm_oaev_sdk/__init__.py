"""Public API surface. Import from here, not from xtm_oaev_sdk._core."""

__version__ = "0.1.0"

# Errors
from ._core.errors import (
    ConfigurationError,
    OpenAEVAuthenticationError,
    OpenAEVCreateError,
    OpenAEVError,
    OpenAEVGetError,
    OpenAEVHeadError,
    OpenAEVHttpError,
    OpenAEVListError,
    OpenAEVParsingError,
    OpenAEVUpdateError,
    RedirectError,
    SignatureTransmissionError,
    on_http_error,
)

# Utils
from ._core.utils import (
    AppLogger,
    AppLoggerProtocol,
    CustomJsonFormatter,
    EncodedId,
    EnhancedJSONEncoder,
    RequiredOptional,
    copy_dict,
    logger,
    remove_none_from_dict,
    setup_logging_config,
)

# Security domain
from ._core.security_domain import SecurityDomains

# Client protocol
from ._core.client_protocol import BaseClient

# Daemon protocol
from ._core.daemon_protocol import DaemonProtocol

# SSL utilities
from ._core.ssl_utils import (
    data_to_temp_file,
    is_memory_certificate,
    ssl_cert_chain,
    ssl_verify_locations,
)

# Configuration
from ._core.configuration import (
    BaseConfigModel,
    CONFIGURATION_TYPES,
    ConfigLoaderCollector,
    ConfigLoaderOAEV,
    Configuration,
    ConfigurationHint,
    ConfigurationProtocol,
)
from ._core.configuration.sources import DictionarySource, EnvironmentSource
from ._core.configuration.settings_loader import (
    HttpUrlToString,
    LogLevelToLower,
    SettingsLoader,
    TimedeltaInSeconds,
)
from ._core.configuration.connector_config_schema_generator import (
    ConnectorConfigSchemaGenerator,
)

# Contracts
from ._core.contracts import (
    Contract,
    ContractAsset,
    ContractAssetGroup,
    ContractAttachment,
    ContractBuilder,
    ContractBuilderProtocol,
    ContractCardinality,
    ContractCardinalityElement,
    ContractCheckbox,
    ContractConfig,
    ContractElement,
    ContractExpectationType,
    ContractExpectations,
    ContractFieldKey,
    ContractFieldType,
    ContractOutputElement,
    ContractOutputType,
    ContractPayload,
    ContractSelect,
    ContractTeam,
    ContractText,
    ContractTextArea,
    ContractTuple,
    ContractVariable,
    Domain,
    Expectation,
    LinkedFieldModel,
    SupportedLanguage,
    VariableHelper,
    VariableType,
    prepare_contracts,
)

# Signatures
from ._core.signatures import (
    CloudInjectorConfig,
    ExecutionDetails,
    ExecutionSignature,
    ExpectationSignatureGroup,
    ExtraSignatureData,
    InjectExecutionActions,
    InjectorConfig,
    MatchTypes,
    NetworkInjectorConfig,
    SignatureCallbackPayload,
    SignatureExpectationType,
    SignatureManager,
    SignatureManagerProtocol,
    SignatureMatch,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureTransportProtocol,
    SignatureType,
    SignatureTypes,
    SignatureValue,
    TargetSignatures,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
    build_network_configs,
)

__all__ = [
    "__version__",
    # errors
    "ConfigurationError",
    "OpenAEVAuthenticationError",
    "OpenAEVCreateError",
    "OpenAEVError",
    "OpenAEVGetError",
    "OpenAEVHeadError",
    "OpenAEVHttpError",
    "OpenAEVListError",
    "OpenAEVParsingError",
    "OpenAEVUpdateError",
    "RedirectError",
    "SignatureTransmissionError",
    "on_http_error",
    # utils
    "AppLogger",
    "AppLoggerProtocol",
    "CustomJsonFormatter",
    "EncodedId",
    "EnhancedJSONEncoder",
    "RequiredOptional",
    "copy_dict",
    "logger",
    "remove_none_from_dict",
    "setup_logging_config",
    # security_domain
    "SecurityDomains",
    # client_protocol
    "BaseClient",
    # daemon_protocol
    "DaemonProtocol",
    # ssl_utils
    "data_to_temp_file",
    "is_memory_certificate",
    "ssl_cert_chain",
    "ssl_verify_locations",
    # configuration
    "BaseConfigModel",
    "CONFIGURATION_TYPES",
    "ConfigLoaderCollector",
    "ConfigLoaderOAEV",
    "Configuration",
    "ConfigurationHint",
    "ConfigurationProtocol",
    "ConnectorConfigSchemaGenerator",
    "DictionarySource",
    "EnvironmentSource",
    "HttpUrlToString",
    "LogLevelToLower",
    "SettingsLoader",
    "TimedeltaInSeconds",
    # contracts
    "Contract",
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
    "ContractSelect",
    "ContractTeam",
    "ContractText",
    "ContractTextArea",
    "ContractTuple",
    "ContractVariable",
    "Domain",
    "Expectation",
    "LinkedFieldModel",
    "SupportedLanguage",
    "VariableHelper",
    "VariableType",
    "prepare_contracts",
    # signatures
    "CloudInjectorConfig",
    "ExecutionDetails",
    "ExecutionSignature",
    "ExpectationSignatureGroup",
    "ExtraSignatureData",
    "InjectExecutionActions",
    "InjectorConfig",
    "MatchTypes",
    "NetworkInjectorConfig",
    "SignatureCallbackPayload",
    "SignatureExpectationType",
    "SignatureManager",
    "SignatureManagerProtocol",
    "SignatureMatch",
    "SignatureOutputStructure",
    "SignaturePayload",
    "SignatureTarget",
    "SignatureTransportProtocol",
    "SignatureType",
    "SignatureTypes",
    "SignatureValue",
    "TargetSignatures",
    "ToolErrorInfo",
    "ToolOutput",
    "ToolTimeoutInfo",
    "build_network_configs",
]
