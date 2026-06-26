"""BaseClient Protocol — behavioral contract for OpenAEV HTTP client implementations."""

from typing import Any, Protocol, runtime_checkable


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
    def per_page(self) -> int: ...

    @property
    def pagination(self) -> str: ...

    @property
    def order_by(self) -> str: ...

    @property
    def url(self) -> str: ...

    @property
    def headers(self) -> dict[str, str]: ...

    @property
    def ssl_verify(self) -> bool | str: ...

    @property
    def timeout(self) -> int | float | None: ...

    @property
    def tenant_id(self) -> str | None: ...

    @property
    def session(self) -> Any:
        """The underlying HTTP session (e.g. requests.Session)."""
        ...

    @property
    def backend(self) -> Any:
        """The HTTP backend implementation handling transport."""
        ...

    def http_head(self, path: str, **kwargs: Any) -> Any: ...

    def http_get(self, path: str, **kwargs: Any) -> Any: ...

    def http_post(self, path: str, **kwargs: Any) -> Any: ...

    def http_patch(self, path: str, **kwargs: Any) -> Any: ...

    def http_put(self, path: str, **kwargs: Any) -> Any: ...

    def http_delete(self, path: str, **kwargs: Any) -> Any: ...

    def http_list(self, path: str, **kwargs: Any) -> Any: ...
