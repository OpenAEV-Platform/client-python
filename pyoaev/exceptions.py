"""DEPRECATED: the error types moved to :mod:`xtm_oaev_sdk`.

Backward-compatibility shim: every error name below resolves to the *identical*
xtm_oaev_sdk object and emits a :class:`DeprecationWarning` on access.
``on_http_error`` is a REST client helper and stays defined here.
"""

import functools
from typing import Any, Callable, Type, TypeVar, cast

import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import OpenAEVHttpError as _OpenAEVHttpError
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

# Unchanged public export list of the legacy module (also extended into
# ``pyoaev.__all__``); ``OpenAEVError`` and ``on_http_error`` were reachable
# but never exported.
__all__ = [  # noqa: F822 (names are served by the PEP 562 __getattr__ below)
    "ConfigurationError",
    "OpenAEVAuthenticationError",
    "OpenAEVHttpError",
    "OpenAEVParsingError",
    "RedirectError",
    "OpenAEVHeadError",
    "OpenAEVListError",
    "OpenAEVGetError",
    "OpenAEVUpdateError",
    "OpenAEVCreateError",
    "OpenAEVDeleteError",
    "SignatureTransmissionError",
]

_MOVED = [*__all__, "OpenAEVError"]

# For an explanation of how these type-hints work see:
# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
#
# The goal here is that functions which get decorated will retain their types.
__F = TypeVar("__F", bound=Callable[..., Any])


def on_http_error(error: Type[Exception]) -> Callable[[__F], __F]:
    def wrap(f: __F) -> __F:
        @functools.wraps(f)
        def wrapped_f(*args: Any, **kwargs: Any) -> Any:
            try:
                return f(*args, **kwargs)
            except _OpenAEVHttpError as e:
                raise error(e.error_message, e.response_code, e.response_body) from e

        return cast(__F, wrapped_f)

    return wrap


__getattr__ = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in _MOVED
    },
    module_name=__name__,
)
