"""xtm-oaev-sdk shared utilities.

Core utility classes and functions used across the SDK engine modules.
Provides logging infrastructure, JSON encoding, data validation helpers,
and dict manipulation utilities.

Public symbols (re-exported from xtm_oaev_sdk):
    - AppLogger: Structured JSON logger with level-aware output.
    - AppLoggerProtocol: Protocol for logger behavioral contract.
    - EnhancedJSONEncoder: JSON encoder supporting dataclasses and Pydantic models.
    - RequiredOptional: Immutable field-presence validator.
    - EncodedId: URL-safe encoded identifier type.
    - CustomJsonFormatter: Timestamped JSON log formatter.
    - setup_logging_config: Configure root logger with JSON or plain output.
    - copy_dict: Flatten nested dict into bracket-notation keys.
    - remove_none_from_dict: Strip None-valued keys from a dict.
    - logger: DEPRECATED — use AppLogger directly.
"""

import dataclasses
import datetime
import json
import logging
import warnings
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict
from pythonjsonlogger.json import JsonFormatter

__all__ = [
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
]


@runtime_checkable
class AppLoggerProtocol(Protocol):
    """Behavioral contract for SDK logging services.

    Any logger implementation used by SDK consumers must satisfy this
    protocol. The built-in AppLogger class implements it.

    The __call__ method allows switching the logger name (factory pattern):
        >>> log = AppLogger(logging.DEBUG)
        >>> module_log = log("my_module")  # returns self with new name
    """

    def __call__(self, name: str) -> "AppLoggerProtocol":
        """Switch logger name and return self."""
        ...

    def debug(self, message: str, meta: Any = None) -> None:
        """Log at DEBUG level."""
        ...

    def info(self, message: str, meta: Any = None) -> None:
        """Log at INFO level."""
        ...

    def warning(self, message: str, meta: Any = None) -> None:
        """Log at WARNING level."""
        ...

    def error(self, message: str, meta: Any = None) -> None:
        """Log at ERROR level with traceback."""
        ...

    @staticmethod
    def setup_logger_level(lib: str, log_level: int) -> None:
        """Override log level for a third-party library."""
        ...


class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles dataclasses and Pydantic models.

    Extends the default encoder to serialize:
    - ``@dataclass`` instances via ``dataclasses.asdict()``
    - ``pydantic.BaseModel`` instances via ``.model_dump()``

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
        """Serialize dataclasses and Pydantic models to dicts.

        Args:
            o: Object to serialize.

        Returns:
            A JSON-serializable representation.

        Raises:
            TypeError: If the object is not serializable.
        """
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return dataclasses.asdict(o)
        if isinstance(o, BaseModel):
            return o.model_dump()
        return super().default(o)


class RequiredOptional(BaseModel):
    """Immutable field-presence validator for API payloads.

    Validates that required fields are present, optional fields are allowed,
    and exclusive fields follow mutual exclusion rules.

    Args:
        required: Tuple of field names that must be present.
        optional: Tuple of field names that may be present.
        exclusive: Tuple of field names where exactly one must be present.

    Example:
        >>> ro = RequiredOptional(required=("name", "type"), exclusive=("id", "key"))
        >>> ro.validate_attrs(data={"name": "x", "type": "y", "id": "123"})  # OK
        >>> ro.validate_attrs(data={"name": "x"})  # raises AttributeError
    """

    model_config = ConfigDict(frozen=True)

    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()
    exclusive: tuple[str, ...] = ()

    def validate_attrs(
        self,
        *,
        data: dict[str, Any],
        excludes: list[str] | None = None,
    ) -> None:
        """Validate field presence against the configured rules.

        Args:
            data: Dict of field names to values to validate.
            excludes: Field names to skip during required-field checks.

        Raises:
            AttributeError: If required fields are missing, or exclusive
                field constraints are violated.
        """
        if excludes is None:
            excludes = []

        if self.required:
            required = [k for k in self.required if k not in excludes]
            missing = [attr for attr in required if attr not in data]
            if missing:
                raise AttributeError(f"Missing attributes: {', '.join(missing)}")

        if self.exclusive:
            exclusives = [attr for attr in data if attr in self.exclusive]
            if len(exclusives) > 1:
                raise AttributeError(
                    f"Provide only one of these attributes: {', '.join(exclusives)}"
                )
            if not exclusives:
                raise AttributeError(
                    f"Must provide one of these attributes: "
                    f"{', '.join(self.exclusive)}"
                )


class EncodedId(str):
    """URL-safe encoded identifier.

    Wraps a string or integer value with URL percent-encoding applied.
    Idempotent: encoding an already-encoded value returns it unchanged.

    Args:
        value: The raw identifier to encode. Accepts str, int, or EncodedId.

    Raises:
        TypeError: If value is not str, int, or EncodedId.

    Example:
        >>> EncodedId("hello world")
        'hello%20world'
        >>> EncodedId(42)
        '42'
    """

    def __new__(cls, value: "str | int | EncodedId") -> "EncodedId":
        if isinstance(value, EncodedId):
            return value

        if not isinstance(value, (int, str)):
            raise TypeError(f"Unsupported type received: {type(value)}")

        import urllib.parse

        if isinstance(value, str):
            value = urllib.parse.quote(value, safe="")
        return super().__new__(cls, value)


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
    return {k: v for k, v in data.items() if v is not None}


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
    for k, v in src.items():
        if isinstance(v, dict):
            for dict_k, dict_v in v.items():
                dest[f"{k}[{dict_k}]"] = dict_v
        else:
            dest[k] = v


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
        if not log_record.get("timestamp"):
            now = datetime.datetime.now(datetime.UTC).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            log_record["timestamp"] = now
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def setup_logging_config(level: int, json_logging: bool = True) -> None:
    """Configure root logger with JSON or plain text output.

    Silences noisy third-party loggers (urllib3, pika) and sets up
    the root logger with either structured JSON or basic text formatting.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        json_logging: If True, use CustomJsonFormatter for structured output.
            If False, use basicConfig plain text.
    """
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("pika").setLevel(logging.ERROR)
    if json_logging:
        log_handler = logging.StreamHandler()
        log_handler.setLevel(level)
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
        log_handler.setFormatter(formatter)
        logging.basicConfig(handlers=[log_handler], level=level, force=True)
    else:
        logging.basicConfig(level=level)


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
        self.local_logger = logging.getLogger(name)

    def __call__(self, name: str) -> "AppLogger":
        """Switch to a named logger instance.

        Args:
            name: New logger name.

        Returns:
            Self with updated logger name.
        """
        self.local_logger = logging.getLogger(name)
        return self

    @staticmethod
    def prepare_meta(meta: Any = None) -> dict[str, Any] | None:
        """Wrap metadata for structured logging extra field.

        Args:
            meta: Arbitrary metadata to attach to log entry.

        Returns:
            Dict with 'attributes' key, or None if no metadata.
        """
        return None if meta is None else {"attributes": meta}

    @staticmethod
    def setup_logger_level(lib: str, log_level: int) -> None:
        """Override log level for a third-party library.

        Args:
            lib: Library logger name (e.g., "urllib3").
            log_level: Desired logging level.
        """
        logging.getLogger(lib).setLevel(log_level)

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

    .. deprecated::
        Use ``AppLogger(level, json_logging)`` directly instead.
        This function will be removed in a future release.

    Args:
        level: Logging level.
        json_logging: Whether to use JSON output.

    Returns:
        An AppLogger instance.
    """
    warnings.warn(
        "logger() is deprecated. Use AppLogger(level, json_logging) directly. "
        "This function will be removed in a future release.",
        DeprecationWarning,
        stacklevel=2,
    )
    return AppLogger(level, json_logging)
