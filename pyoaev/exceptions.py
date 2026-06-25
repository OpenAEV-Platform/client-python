"""Backward-compat shim — use 'from xtm_oaev_sdk import ...' instead."""

from typing_extensions import deprecated

from xtm_oaev_sdk import (
    ConfigurationError as _ConfigurationError,
    OpenAEVAuthenticationError as _OpenAEVAuthenticationError,
    OpenAEVCreateError as _OpenAEVCreateError,
    OpenAEVDeleteError as _OpenAEVDeleteError,
    OpenAEVError as _OpenAEVError,
    OpenAEVGetError as _OpenAEVGetError,
    OpenAEVHeadError as _OpenAEVHeadError,
    OpenAEVHttpError as _OpenAEVHttpError,
    OpenAEVListError as _OpenAEVListError,
    OpenAEVParsingError as _OpenAEVParsingError,
    OpenAEVUpdateError as _OpenAEVUpdateError,
    RedirectError as _RedirectError,
    SignatureTransmissionError as _SignatureTransmissionError,
    on_http_error as _on_http_error,
)

ConfigurationError = deprecated("Use 'from xtm_oaev_sdk import ConfigurationError' instead.", category=DeprecationWarning)(_ConfigurationError)
OpenAEVAuthenticationError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVAuthenticationError' instead.", category=DeprecationWarning)(_OpenAEVAuthenticationError)
OpenAEVCreateError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVCreateError' instead.", category=DeprecationWarning)(_OpenAEVCreateError)
OpenAEVDeleteError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVDeleteError' instead.", category=DeprecationWarning)(_OpenAEVDeleteError)
OpenAEVError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVError' instead.", category=DeprecationWarning)(_OpenAEVError)
OpenAEVGetError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVGetError' instead.", category=DeprecationWarning)(_OpenAEVGetError)
OpenAEVHeadError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVHeadError' instead.", category=DeprecationWarning)(_OpenAEVHeadError)
OpenAEVHttpError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVHttpError' instead.", category=DeprecationWarning)(_OpenAEVHttpError)
OpenAEVListError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVListError' instead.", category=DeprecationWarning)(_OpenAEVListError)
OpenAEVParsingError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVParsingError' instead.", category=DeprecationWarning)(_OpenAEVParsingError)
OpenAEVUpdateError = deprecated("Use 'from xtm_oaev_sdk import OpenAEVUpdateError' instead.", category=DeprecationWarning)(_OpenAEVUpdateError)
RedirectError = deprecated("Use 'from xtm_oaev_sdk import RedirectError' instead.", category=DeprecationWarning)(_RedirectError)
SignatureTransmissionError = deprecated("Use 'from xtm_oaev_sdk import SignatureTransmissionError' instead.", category=DeprecationWarning)(_SignatureTransmissionError)
on_http_error = deprecated("Use 'from xtm_oaev_sdk import on_http_error' instead.", category=DeprecationWarning)(_on_http_error)

__all__ = [
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
]
