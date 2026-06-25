"""Backward-compatibility shim.

All symbols have moved to ``xtm_oaev_sdk``. This module re-exports them
for existing consumers. Prefer direct imports::

    from xtm_oaev_sdk import OpenAEVError, OpenAEVHttpError, ...
"""

import warnings

warnings.warn(
    "Importing from 'pyoaev.exceptions' is deprecated. "
    "Use 'from xtm_oaev_sdk import ...' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from xtm_oaev_sdk import (
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

__all__ = [
    "ConfigurationError",
    "on_http_error",
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
]
