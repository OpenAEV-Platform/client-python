"""DaemonProtocol — behavioral contract for daemon implementations.

Defines the shared lifecycle surface that both collector and injector
daemons expose. Extension SDKs type-hint against this Protocol instead
of importing the concrete BaseDaemon from pyoaev.
"""

from typing import Any, Callable, Protocol, runtime_checkable


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

    def start(self) -> None: ...

    def set_callback(self, callback: Callable[..., Any]) -> None: ...

    def get_id(self) -> str | None: ...
