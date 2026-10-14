"""BaseClient Protocol — behavioral contract for OpenAEV HTTP client implementations."""

from typing import Any, Protocol, runtime_checkable

__all__ = ["BaseClient"]


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
