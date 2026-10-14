"""Utilities specific to the pyoaev HTTP client.

The shared utilities moved to :mod:`xtm_oaev_sdk`; their legacy names here
resolve to the *identical* SDK objects and emit a :class:`DeprecationWarning`
on access.
"""

import email.message
from typing import Any, Callable, Iterator, Optional, Union

import requests
import xtm_oaev_sdk as _sdk
from xtm_oaev_sdk import make_deprecated_getattr as _make_deprecated_getattr

_MOVED = [
    "AppLogger",
    "CustomJsonFormatter",
    "EncodedId",
    "EnhancedJSONEncoder",
    "RequiredOptional",
    "copy_dict",
    "logger",
    "remove_none_from_dict",
    "setup_logging_config",
    "PingAlive",
]

__all__ = [  # noqa: F822 (moved names are served by the PEP 562 __getattr__ below)
    "get_content_type",
    "response_content",
    *_MOVED,
]


class _StdoutStream:
    def __call__(self, chunk: Any) -> None:
        print(chunk)


def get_content_type(content_type: Optional[str]) -> str:
    message = email.message.Message()
    message["content-type"] = content_type

    return message.get_content_type()


def response_content(
    response: requests.Response,
    streamed: bool,
    action: Optional[Callable[[bytes], None]],
    chunk_size: int,
    *,
    iterator: bool,
) -> Optional[Union[bytes, Iterator[Any]]]:
    if iterator:
        return response.iter_content(chunk_size=chunk_size)

    if streamed is False:
        return response.content

    if action is None:
        action = _StdoutStream()

    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            action(chunk)
    return None


__getattr__ = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in _MOVED
    },
    module_name=__name__,
)
