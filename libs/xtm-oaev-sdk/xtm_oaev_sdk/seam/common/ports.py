"""Common ports: the behaviour the public adapters expect from the core."""

import logging
import ssl
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "CertificatesPort",
    "DictToolsPort",
    "JsonEncodingPort",
    "LoggingPort",
]


@runtime_checkable
class JsonEncodingPort(Protocol):
    """Encodes the objects the standard JSON encoder does not support."""

    def encode_default(self, o: Any) -> Any:
        """JSON-serializable form of ``o``; TypeError when unsupported."""


@runtime_checkable
class LoggingPort(Protocol):
    """Configures and feeds the standard logging machinery."""

    def setup_logging_config(
        self,
        level: int,
        json_logging: bool,
        formatter_class: type[logging.Formatter],
    ) -> None:
        """Configure the root logger, as JSON with ``formatter_class`` or text."""

    def get_logger(self, name: str) -> logging.Logger:
        """The named standard logger."""

    def prepare_meta(self, meta: Any) -> dict[str, Any] | None:
        """The ``extra`` mapping carrying the structured metadata."""

    def set_library_level(self, lib: str, log_level: int) -> None:
        """Override the log level of a third-party library."""

    def complete_record(
        self, log_record: dict[str, Any], record: logging.LogRecord
    ) -> None:
        """Add the timestamp and uppercase level fields of a JSON record."""


@runtime_checkable
class DictToolsPort(Protocol):
    """Reshapes the dictionaries exchanged with the platform."""

    def copy_dict(self, *, src: dict[str, Any], dest: dict[str, Any]) -> None:
        """Copy ``src`` into ``dest``, flattening nested dicts as ``key[sub]``."""

    def remove_none_from_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """New dict without the None-valued entries."""


@runtime_checkable
class CertificatesPort(Protocol):
    """Loads certificates, files or in-memory PEM data, into SSL contexts."""

    def data_to_temp_file(self, data: str) -> str:
        """Path of a new owner-only temporary file holding ``data``."""

    def is_memory_certificate(self, certificate: str) -> bool:
        """Whether ``certificate`` is PEM data rather than a file path."""

    def ssl_cert_chain(
        self,
        ssl_context: ssl.SSLContext,
        cert_data: str | None,
        key_data: str | None,
        passphrase: str | None,
    ) -> None:
        """Load a certificate chain into ``ssl_context``."""

    def ssl_verify_locations(
        self, ssl_context: ssl.SSLContext, certdata: str | None
    ) -> None:
        """Load CA verification locations into ``ssl_context``."""
