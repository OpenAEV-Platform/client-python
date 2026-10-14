"""Shared contracts: errors, enums, type aliases, and the concrete utility
layer."""

from xtm_oaev_sdk._core.asset_types import (
    AssetCategory,
    AssetCriticality,
    AssetSubCategory,
    CloudProvider,
)
from xtm_oaev_sdk._core.errors import (
    ConfigurationError,
    OpenAEVAuthenticationError,
    OpenAEVCreateError,
    OpenAEVDeleteError,
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
from xtm_oaev_sdk._core.security_domain import SecurityDomains
from xtm_oaev_sdk._core.ssl_utils import (
    data_to_temp_file,
    is_memory_certificate,
    ssl_cert_chain,
    ssl_verify_locations,
)
from xtm_oaev_sdk._core.utils import (
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

__all__ = [
    # Errors
    "ConfigurationError",
    "OpenAEVAuthenticationError",
    "OpenAEVCreateError",
    "OpenAEVDeleteError",
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
    # Protocols
    "AppLoggerProtocol",
    # Types
    "EncodedId",
    "RequiredOptional",
    # Enums
    "AssetCategory",
    "AssetCriticality",
    "AssetSubCategory",
    "CloudProvider",
    "SecurityDomains",
    # Behaviour (concrete adapters)
    "AppLogger",
    "CustomJsonFormatter",
    "EnhancedJSONEncoder",
    "copy_dict",
    "data_to_temp_file",
    "is_memory_certificate",
    "logger",
    "remove_none_from_dict",
    "setup_logging_config",
    "ssl_cert_chain",
    "ssl_verify_locations",
]
