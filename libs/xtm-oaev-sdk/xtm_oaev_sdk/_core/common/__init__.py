"""Shared implementations: errors, utils, SSL, protocols, enums."""

from xtm_oaev_sdk._core.errors import on_http_error
from xtm_oaev_sdk._core.utils import (
    AppLogger,
    CustomJsonFormatter,
    EnhancedJSONEncoder,
    copy_dict,
    logger,
    remove_none_from_dict,
    setup_logging_config,
)
from xtm_oaev_sdk._core.ssl_utils import (
    data_to_temp_file,
    is_memory_certificate,
    ssl_cert_chain,
    ssl_verify_locations,
)

__all__ = [
    "AppLogger",
    "CustomJsonFormatter",
    "EnhancedJSONEncoder",
    "copy_dict",
    "data_to_temp_file",
    "is_memory_certificate",
    "logger",
    "on_http_error",
    "remove_none_from_dict",
    "setup_logging_config",
    "ssl_cert_chain",
    "ssl_verify_locations",
]
