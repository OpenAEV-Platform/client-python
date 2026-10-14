"""Common adapters: HTTP error translation, logging, JSON encoding, dict and
certificate helpers, plus the shared errors, enums, value objects and
protocols of the common seam.

Each adapter speaks the common seam types and delegates to the core
implementation of its port.
"""

import functools
import json
import logging
import ssl
from typing import Any, Callable, Type, TypeVar, cast

from pythonjsonlogger.json import JsonFormatter
from xtm_oaev_sdk._core.common import (
    Certificates,
    DictTools,
    HttpErrorTranslator,
    JsonEncoding,
    LoggingSetup,
)
from xtm_oaev_sdk.seam.common import (
    AppLoggerProtocol,
    AssetCategory,
    AssetCriticality,
    AssetSubCategory,
    BaseClient,
    CertificatesPort,
    CloudProvider,
    ConfigurationError,
    DaemonProtocol,
    DictToolsPort,
    EncodedId,
    HttpErrorPort,
    JsonEncodingPort,
    LoggingPort,
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
    RequiredOptional,
    SecurityDomains,
    SignatureTransmissionError,
)

__all__ = [
    "AppLogger",
    "AppLoggerProtocol",
    "AssetCategory",
    "AssetCriticality",
    "AssetSubCategory",
    "BaseClient",
    "CloudProvider",
    "ConfigurationError",
    "CustomJsonFormatter",
    "DaemonProtocol",
    "EncodedId",
    "EnhancedJSONEncoder",
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
    "RequiredOptional",
    "SecurityDomains",
    "SignatureTransmissionError",
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

_http_errors: HttpErrorPort = HttpErrorTranslator()
_encoding: JsonEncodingPort = JsonEncoding()
_logging: LoggingPort = LoggingSetup()
_dicts: DictToolsPort = DictTools()
_certificates: CertificatesPort = Certificates()

_F = TypeVar("_F", bound=Callable[..., Any])


def on_http_error(error: Type[Exception]) -> Callable[[_F], _F]:
    """Decorator that wraps OpenAEVHttpError into a caller-specified type.

    Use on API methods to convert generic HTTP errors into operation-specific
    exception types while preserving error context.

    Args:
        error: The exception class to raise instead of OpenAEVHttpError.
            Must accept (error_message, response_code, response_body) args.

    Returns:
        A decorator that wraps the target function.

    Example:
        >>> @on_http_error(OpenAEVCreateError)
        ... def create_entity(self, data):
        ...     return self._post("/entities", data)
    """

    def wrap(f: _F) -> _F:
        @functools.wraps(f)
        def wrapped_f(*args: Any, **kwargs: Any) -> Any:
            return _http_errors.call(f, error, *args, **kwargs)

        return cast(_F, wrapped_f)

    return wrap


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that serializes ``@dataclass`` instances via
    ``dataclasses.asdict()``.

    Example:
        >>> import json
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class Point:
        ...     x: int
        ...     y: int
        >>> json.dumps(Point(1, 2), cls=EnhancedJSONEncoder)
        '{"x": 1, "y": 2}'
    """

    def default(self, o: Any) -> Any:
        """Serialize dataclasses to dicts.

        Args:
            o: Object to serialize.

        Returns:
            A JSON-serializable representation.

        Raises:
            TypeError: If the object is not serializable.
        """
        return _encoding.encode_default(o)


def remove_none_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Remove all keys with None values from a dict.

    Args:
        data: Source dictionary.

    Returns:
        New dictionary with None-valued entries removed.

    Example:
        >>> remove_none_from_dict({"a": 1, "b": None, "c": "x"})
        {'a': 1, 'c': 'x'}
    """
    return _dicts.remove_none_from_dict(data)


def copy_dict(*, src: dict[str, Any], dest: dict[str, Any]) -> None:
    """Flatten nested dict values into bracket-notation keys.

    For nested dicts, expands ``{"key": {"sub": "val"}}`` into
    ``dest["key[sub]"] = "val"``. Non-dict values copy directly.

    Args:
        src: Source dictionary to copy from.
        dest: Destination dictionary to copy into (mutated in place).

    Example:
        >>> dest = {}
        >>> copy_dict(src={"filters": {"type": "malware"}}, dest=dest)
        >>> dest
        {'filters[type]': 'malware'}
    """
    _dicts.copy_dict(src=src, dest=dest)


class CustomJsonFormatter(JsonFormatter):
    """JSON log formatter with ISO timestamp and uppercase level.

    Extends pythonjsonlogger's JsonFormatter to add:
    - UTC ISO 8601 timestamp if not already present.
    - Uppercase level field normalization.
    """

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Add timestamp and level fields to the log record.

        Args:
            log_record: The output dict being built.
            record: The stdlib LogRecord.
            message_dict: Extra message fields.
        """
        super().add_fields(log_record, record, message_dict)
        _logging.complete_record(log_record, record)


def setup_logging_config(level: int, json_logging: bool = True) -> None:
    """Configure root logger with JSON or plain text output.

    Silences noisy third-party loggers (urllib3, pika) and sets up
    the root logger with either structured JSON or basic text formatting.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        json_logging: If True, use CustomJsonFormatter for structured output.
            If False, use basicConfig plain text.
    """
    _logging.setup_logging_config(level, json_logging, CustomJsonFormatter)


class AppLogger:
    """Structured application logger with JSON support.

    Provides a simple logging interface with optional JSON formatting
    and metadata attachment. Supports name-switching via __call__ for
    per-module logger instances.

    Args:
        level: Logging level (e.g., logging.DEBUG).
        json_logging: Whether to use JSON-formatted output.
        name: Logger name (defaults to module name).

    Example:
        >>> log = AppLogger(logging.INFO)
        >>> log.info("Server started", {"port": 8080})
        >>> module_log = log("my_module")
        >>> module_log.debug("Processing request")
    """

    def __init__(self, level: int, json_logging: bool = True, name: str = __name__):
        self.log_level = level
        self.json_logging = json_logging
        setup_logging_config(self.log_level, self.json_logging)
        self.local_logger = _logging.get_logger(name)

    def __call__(self, name: str) -> "AppLogger":
        """Switch to a named logger instance.

        Args:
            name: New logger name.

        Returns:
            Self with updated logger name.
        """
        self.local_logger = _logging.get_logger(name)
        return self

    @staticmethod
    def prepare_meta(meta: Any = None) -> dict[str, Any] | None:
        """Wrap metadata for structured logging extra field.

        Args:
            meta: Arbitrary metadata to attach to log entry.

        Returns:
            Dict with 'attributes' key, or None if no metadata.
        """
        return _logging.prepare_meta(meta)

    @staticmethod
    def setup_logger_level(lib: str, log_level: int) -> None:
        """Override log level for a third-party library.

        Args:
            lib: Library logger name (e.g., "urllib3").
            log_level: Desired logging level.
        """
        _logging.set_library_level(lib, log_level)

    def debug(self, message: str, meta: Any = None) -> None:
        """Log at DEBUG level.

        Args:
            message: Log message.
            meta: Optional structured metadata.
        """
        self.local_logger.debug(message, extra=AppLogger.prepare_meta(meta))

    def info(self, message: str, meta: Any = None) -> None:
        """Log at INFO level.

        Args:
            message: Log message.
            meta: Optional structured metadata.
        """
        self.local_logger.info(message, extra=AppLogger.prepare_meta(meta))

    def warning(self, message: str, meta: Any = None) -> None:
        """Log at WARNING level.

        Args:
            message: Log message.
            meta: Optional structured metadata.
        """
        self.local_logger.warning(message, extra=AppLogger.prepare_meta(meta))

    def error(self, message: str, meta: Any = None) -> None:
        """Log at ERROR level with traceback.

        Args:
            message: Log message.
            meta: Optional structured metadata.
        """
        self.local_logger.error(message, exc_info=1, extra=AppLogger.prepare_meta(meta))


def logger(level: int, json_logging: bool = True) -> AppLogger:
    """Create an AppLogger instance.

    Args:
        level: Logging level.
        json_logging: Whether to use JSON output.

    Returns:
        An AppLogger instance.
    """
    return AppLogger(level, json_logging)


def data_to_temp_file(data: str) -> str:
    """Write data to a secure temporary file and return its path."""
    return _certificates.data_to_temp_file(data)


def is_memory_certificate(certificate: str) -> bool:
    """Return True if the certificate is PEM-encoded in memory (not a file path)."""
    return _certificates.is_memory_certificate(certificate)


def ssl_cert_chain(
    ssl_context: ssl.SSLContext,
    cert_data: str | None,
    key_data: str | None,
    passphrase: str | None,
) -> None:
    """Load a certificate chain into an SSL context, handling in-memory PEM data."""
    _certificates.ssl_cert_chain(ssl_context, cert_data, key_data, passphrase)


def ssl_verify_locations(ssl_context: ssl.SSLContext, certdata: str | None) -> None:
    """Load CA verification locations into an SSL context."""
    _certificates.ssl_verify_locations(ssl_context, certdata)
