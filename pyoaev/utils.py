"""Utilities specific to the pyoaev HTTP client and daemons.

The shared utilities moved to :mod:`xtm_oaev_sdk`; their legacy names here
resolve to the *identical* SDK objects and emit a :class:`DeprecationWarning`
on access.
"""

import email.message
import threading
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
]

__all__ = [  # noqa: F822 (moved names are served by the PEP 562 __getattr__ below)
    "get_content_type",
    "response_content",
    "PingAlive",
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


class PingAlive(threading.Thread):
    def __init__(self, api, config, logger, ping_type) -> None:
        threading.Thread.__init__(self)
        self.ping_type = ping_type
        self.api = api
        self.tenant_id = getattr(self.api, "tenant_id", None)
        self.config = config
        self.logger = logger
        self.in_error = False
        self.exit_event = threading.Event()

    def ping(self) -> None:
        while not self.exit_event.is_set():
            try:
                if self.ping_type == "injector":
                    self.api.injector.create(self.config, False)
                else:
                    self.api.collector.create(self.config, False)
            except Exception as err:  # pylint: disable=broad-except
                self.logger.error("Error pinging the API: " + str(err))
            self.exit_event.wait(40)

    def run(self) -> None:
        self.logger.info(
            "Starting PingAlive thread",
            {"tenant_id": str(self.tenant_id) if self.tenant_id else None},
        )
        self.ping()

    def stop(self) -> None:
        self.logger.info(
            "Preparing PingAlive for clean shutdown",
            {"tenant_id": str(self.tenant_id) if self.tenant_id else None},
        )
        self.exit_event.set()


__getattr__ = _make_deprecated_getattr(
    {
        name: (f"Use 'from xtm_oaev_sdk import {name}' instead.", getattr(_sdk, name))
        for name in _MOVED
    },
    module_name=__name__,
)
