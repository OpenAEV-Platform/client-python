"""xtm-oaev-sdk error hierarchy.

All SDK exceptions derive from OpenAEVError. Consumers catch specific
subclasses for granular handling or catch the base class as a catch-all.

Exception tree::

    OpenAEVError (base)
    ├── OpenAEVAuthenticationError   — credential/token failures
    ├── OpenAEVHttpError             — generic HTTP transport errors
    │   └── (wrapped by on_http_error decorator into caller-specific types)
    ├── OpenAEVParsingError          — response deserialization failures
    ├── RedirectError                — unexpected HTTP redirects
    ├── OpenAEVHeadError             — HEAD request failures
    ├── OpenAEVGetError              — GET request failures
    ├── OpenAEVUpdateError           — PUT/PATCH request failures
    ├── OpenAEVListError             — list/pagination failures
    ├── OpenAEVCreateError           — POST creation failures
    ├── SignatureTransmissionError   — signature delivery failures
    └── ConfigurationError           — configuration loading/validation failures

Example:
    >>> from xtm_oaev_sdk import OpenAEVError, OpenAEVHttpError
    >>> try:
    ...     api.call()
    ... except OpenAEVHttpError as e:
    ...     print(f"HTTP {e.response_code}: {e.error_message}")
    ... except OpenAEVError as e:
    ...     print(f"SDK error: {e}")
"""

import functools
from typing import TYPE_CHECKING, Any, Callable, Optional, Type, TypeVar, Union, cast


class OpenAEVError(Exception):
    """Base exception for all xtm-oaev-sdk errors.

    Provides structured error context including HTTP status codes and
    response bodies when available. Automatically extracts meaningful
    error messages from JSON response payloads.

    Args:
        error_message: Human-readable error description. Accepts str or bytes.
        response_code: HTTP status code if the error originated from an API call.
        response_body: Raw HTTP response body for deeper error extraction.
    """

    def __init__(
        self,
        error_message: Union[str, bytes] = "",
        response_code: Optional[int] = None,
        response_body: Optional[bytes] = None,
    ) -> None:
        Exception.__init__(self, error_message)
        self.response_code = response_code
        self.response_body = response_body
        try:
            if TYPE_CHECKING:
                assert isinstance(error_message, bytes)
            self.error_message = error_message.decode()
        except Exception:
            if TYPE_CHECKING:
                assert isinstance(error_message, str)
            self.error_message = error_message

    def __str__(self) -> str:
        message = self.error_message

        generic_messages = (
            "Internal Server Error",
            "Bad Request",
            "Not Found",
            "Unauthorized",
            "Forbidden",
            "Service Unavailable",
            "Gateway Timeout",
            "Unknown error",
            "Validation Failed",
        )

        if (
            not message or (message in generic_messages and len(message) < 30)
        ) and self.response_body is not None:
            try:
                import json

                body = self.response_body.decode(errors="ignore")
                data = json.loads(body)
                extracted_msg = None

                if isinstance(data, dict):
                    if "error" in data:
                        err = data.get("error")
                        if isinstance(err, dict) and "message" in err:
                            extracted_msg = err.get("message")
                        elif isinstance(err, str):
                            extracted_msg = err
                    elif "message" in data:
                        extracted_msg = data.get("message")
                    elif "execution_message" in data:
                        extracted_msg = data.get("execution_message")
                    elif "detail" in data:
                        extracted_msg = data.get("detail")
                    elif "errors" in data:
                        errs = data.get("errors")
                        if isinstance(errs, list) and errs:
                            parts = []
                            for item in errs:
                                if isinstance(item, dict) and "message" in item:
                                    parts.append(str(item.get("message")))
                                else:
                                    parts.append(str(item))
                            extracted_msg = "; ".join(parts)
                        elif isinstance(errs, dict):
                            if "children" in errs:
                                validation_errors = []
                                children = errs.get("children", {})
                                for field, field_errors in children.items():
                                    if (
                                        isinstance(field_errors, dict)
                                        and "errors" in field_errors
                                    ):
                                        field_error_list = field_errors.get(
                                            "errors", []
                                        )
                                        if field_error_list:
                                            for err_msg in field_error_list:
                                                validation_errors.append(
                                                    f"{field}: {err_msg}"
                                                )
                                if validation_errors:
                                    base_msg = data.get("message", "Validation Failed")
                                    extracted_msg = (
                                        f"{base_msg}: {'; '.join(validation_errors)}"
                                    )
                            else:
                                parts = []
                                for key, value in errs.items():
                                    if value:
                                        parts.append(f"{key}: {value}")
                                if parts:
                                    extracted_msg = "; ".join(parts)
                        elif isinstance(errs, str):
                            extracted_msg = errs

                if extracted_msg and extracted_msg not in generic_messages:
                    message = str(extracted_msg)
                elif not message:
                    message = body[:500]

            except json.JSONDecodeError:
                if not message or message in generic_messages:
                    try:
                        decoded = self.response_body.decode(errors="ignore")[:500]
                        if decoded and decoded not in generic_messages:
                            message = decoded
                    except Exception:
                        pass
            except Exception:
                pass

        if not message:
            message = "Unknown error"

        message = " ".join(message.split())

        if self.response_code is not None:
            return f"{self.response_code}: {message}"
        return f"{message}"


class OpenAEVAuthenticationError(OpenAEVError):
    """Authentication or authorization failure.

    Raised when credentials are invalid, tokens are expired, or the
    authenticated user lacks permission for the requested operation.
    """

    pass


class OpenAEVHttpError(OpenAEVError):
    """Generic HTTP transport error.

    Raised on unexpected HTTP responses. Use the ``on_http_error``
    decorator to automatically wrap these into operation-specific types.
    """

    pass


class OpenAEVParsingError(OpenAEVError):
    """Response deserialization failure.

    Raised when an API response cannot be parsed into the expected format
    (malformed JSON, unexpected schema, encoding issues).
    """

    pass


class RedirectError(OpenAEVError):
    """Unexpected HTTP redirect encountered."""

    pass


class OpenAEVHeadError(OpenAEVError):
    """HEAD request failure."""

    pass


class OpenAEVGetError(OpenAEVError):
    """GET request failure."""

    pass


class OpenAEVUpdateError(OpenAEVError):
    """PUT/PATCH update request failure."""

    pass


class OpenAEVListError(OpenAEVError):
    """List/pagination request failure."""

    pass


class OpenAEVCreateError(OpenAEVError):
    """POST creation request failure."""

    pass


class SignatureTransmissionError(OpenAEVError):
    """Signature delivery failure.

    Raised when signatures cannot be transmitted to the platform.
    Validation rejected them, 4xx slammed the door, or retries ran dry.
    """

    pass


class ConfigurationError(OpenAEVError):
    """Configuration loading or validation failure.

    Raised when required configuration keys are missing, values fail
    validation, or configuration sources are unreachable.
    """

    pass


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
            try:
                return f(*args, **kwargs)
            except OpenAEVHttpError as e:
                raise error(e.error_message, e.response_code, e.response_body) from e

        return cast(_F, wrapped_f)

    return wrap


__all__ = [
    "OpenAEVError",
    "OpenAEVAuthenticationError",
    "OpenAEVHttpError",
    "OpenAEVParsingError",
    "RedirectError",
    "OpenAEVHeadError",
    "OpenAEVGetError",
    "OpenAEVUpdateError",
    "OpenAEVListError",
    "OpenAEVCreateError",
    "SignatureTransmissionError",
    "ConfigurationError",
    "on_http_error",
]
