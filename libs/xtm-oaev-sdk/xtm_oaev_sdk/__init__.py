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
    AppLoggerProtocol,
    EncodedId,
    EnhancedJSONEncoder,
    RequiredOptional,
    copy_dict,
    remove_none_from_dict,
)

# Security domain
from ._core.security_domain import SecurityDomains

# Configuration
from ._core.configuration import ConfigurationHint, ConfigurationProtocol

# Contracts
from ._core.contracts import ContractBuilderProtocol, ContractExpectationType

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
    "AppLoggerProtocol",
    "EncodedId",
    "EnhancedJSONEncoder",
    "RequiredOptional",
    "copy_dict",
    "remove_none_from_dict",
    # security_domain
    "SecurityDomains",
    # configuration
    "ConfigurationHint",
    "ConfigurationProtocol",
    # contracts
    "ContractBuilderProtocol",
    "ContractExpectationType",
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
