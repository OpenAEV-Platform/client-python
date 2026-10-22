"""Consumer-facing protocols: the API client, daemons and loggers.

Extension SDKs and consumers type-hint against these protocols instead of a
concrete implementation.
"""

from typing import Any, Callable, Protocol, runtime_checkable

__all__ = ["AppLoggerProtocol", "BaseClient", "DaemonProtocol"]


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


@runtime_checkable
class BaseClient(Protocol):
    """Protocol defining the behavioral contract for an OpenAEV HTTP client.

    Any class implementing all methods and properties defined here
    will pass isinstance(obj, BaseClient) checks at runtime.

    IMPORTANT: Properties are used (not bare attributes) to ensure
    isinstance checks work on Python 3.11 where @runtime_checkable
    only inspects methods, not data attributes.
    """

    @property
    def per_page(self) -> int:
        """Number of items per page requested from the API."""

    @property
    def pagination(self) -> str:
        """Pagination mode requested from the API."""

    @property
    def order_by(self) -> str:
        """Sort key requested from the API."""

    @property
    def url(self) -> str:
        """Base URL of the OpenAEV API."""

    @property
    def headers(self) -> dict[str, str]:
        """HTTP headers sent with every request."""

    @property
    def ssl_verify(self) -> bool | str:
        """TLS verification flag or CA bundle path."""

    @property
    def timeout(self) -> int | float | None:
        """Request timeout in seconds."""

    @property
    def tenant_id(self) -> str | None:
        """Tenant scoping the API requests, if any."""

    @property
    def session(self) -> Any:
        """The underlying HTTP session (e.g. requests.Session)."""
        ...

    @property
    def backend(self) -> Any:
        """The HTTP backend implementation handling transport."""
        ...

    def http_head(self, path: str, **kwargs: Any) -> Any:
        """Send a HEAD request."""

    def http_get(self, path: str, **kwargs: Any) -> Any:
        """Send a GET request."""

    def http_post(self, path: str, **kwargs: Any) -> Any:
        """Send a POST request."""

    def http_patch(self, path: str, **kwargs: Any) -> Any:
        """Send a PATCH request."""

    def http_put(self, path: str, **kwargs: Any) -> Any:
        """Send a PUT request."""

    def http_delete(self, path: str, **kwargs: Any) -> Any:
        """Send a DELETE request."""

    def http_list(self, path: str, **kwargs: Any) -> Any:
        """Send a paginated GET request."""


@runtime_checkable
class DaemonProtocol(Protocol):
    """Protocol defining the behavioral contract for a daemon runtime.

    Any class implementing all methods defined here will pass
    isinstance(obj, DaemonProtocol) checks at runtime.

    The three methods capture the public lifecycle surface shared by
    CollectorDaemon and injector daemon runtimes:

    - ``start()`` — run setup then enter the main loop.
    - ``set_callback(callback)`` — configure the periodic callback.
    - ``get_id()`` — return the daemon instance identifier.

    IMPORTANT: Only public methods are part of this contract.
    Implementation details (_setup, _start_loop, _try_callback)
    are excluded — they belong to the concrete daemon class.
    """

    def start(self) -> None:
        """Run the daemon setup, then its main loop."""

    def set_callback(self, callback: Callable[..., Any]) -> None:
        """Configure the callback run by the main loop."""

    def get_id(self) -> str | None:
        """Return the daemon instance identifier."""
