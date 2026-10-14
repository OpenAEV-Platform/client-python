"""Common seam: the shared vocabulary and the common ports.

Errors, enums, value objects and consumer protocols every capability speaks,
plus the ports the common public adapters delegate to. Closed: it imports
nothing from ``xtm_oaev_sdk._core`` nor ``xtm_oaev_sdk.public``. Any change to
these contracts must bump :data:`SEAM_VERSION`.
"""

from xtm_oaev_sdk.seam.common.asset_types import (
    AssetCategory,
    AssetCriticality,
    AssetSubCategory,
    CloudProvider,
)
from xtm_oaev_sdk.seam.common.errors import (
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
from xtm_oaev_sdk.seam.common.ports import (
    CertificatesPort,
    DictToolsPort,
    HttpErrorPort,
    JsonEncodingPort,
    LoggingPort,
)
from xtm_oaev_sdk.seam.common.protocols import (
    AppLoggerProtocol,
    BaseClient,
    DaemonProtocol,
)
from xtm_oaev_sdk.seam.common.security_domains import SecurityDomains
from xtm_oaev_sdk.seam.common.values import EncodedId, RequiredOptional

#: Version of the common seam. Bump on any contract change.
SEAM_VERSION = "1.0.0"

__all__ = [
    "SEAM_VERSION",
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
    # Enums
    "AssetCategory",
    "AssetCriticality",
    "AssetSubCategory",
    "CloudProvider",
    # Enums (security domains)
    "SecurityDomains",
    # Value objects
    "EncodedId",
    "RequiredOptional",
    # Consumer protocols
    "AppLoggerProtocol",
    "BaseClient",
    "DaemonProtocol",
    # Ports
    "CertificatesPort",
    "DictToolsPort",
    "HttpErrorPort",
    "JsonEncodingPort",
    "LoggingPort",
]
