"""Shared contracts: errors, protocols, enums, type aliases."""

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
)
from xtm_oaev_sdk._core.utils import (
    AppLoggerProtocol,
    EncodedId,
    RequiredOptional,
)
from xtm_oaev_sdk._core.client_protocol import BaseClient
from xtm_oaev_sdk._core.daemon_protocol import DaemonProtocol
from xtm_oaev_sdk._core.security_domain import SecurityDomains
from xtm_oaev_sdk._core.asset_types import (
    AssetCategory,
    AssetCriticality,
    AssetSubCategory,
    CloudProvider,
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
    # Protocols
    "AppLoggerProtocol",
    "BaseClient",
    "DaemonProtocol",
    # Types
    "EncodedId",
    "RequiredOptional",
    # Enums
    "AssetCategory",
    "AssetCriticality",
    "AssetSubCategory",
    "CloudProvider",
    "SecurityDomains",
]
