"""Call tape adapter: record a daemon's outside calls to a tape, replay them offline.

tape = CallTape("shodan.tape.json", "record", secrets=configuration.secret_values())
tape.start()
...  # HTTP requests and subprocess.run commands are written to shodan.tape.json
tape.stop()

with CallTape("shodan.tape.json", "replay"):
    ...  # the same calls are answered from shodan.tape.json, offline

lint_tape("shodan.tape.json", secrets=...)  # what looks like a secret left on it
"""

from typing import Any, Sequence

from xtm_oaev_sdk._core.tape import CallTapeEngine
from xtm_oaev_sdk.seam.tape import (
    TAPE_VERSION,
    CallTapePort,
    Tape,
    TapedBody,
    TapedCall,
    TapedCommand,
    TapedHttpCall,
    TapedHttpRequest,
    TapedHttpResponse,
    TapeMissError,
)

__all__ = [
    "CallTape",
    "TAPE_VERSION",
    "Tape",
    "lint_tape",
    "TapeMissError",
    "TapedBody",
    "TapedCall",
    "TapedCommand",
    "TapedHttpCall",
    "TapedHttpRequest",
    "TapedHttpResponse",
]

_tape: CallTapePort = CallTapeEngine()


class CallTape:
    """Records the outside calls of the process to a tape, or replays them.

    In ``record`` mode, HTTP requests (``requests``, urllib3, ``urllib.request``) and
    commands run through ``subprocess.run`` go out as usual, and each call and its
    answer is written to ``path``: one JSON document (``Tape``), a header then the
    calls, rewritten whole after each call. A JSON body is kept as JSON, a compressed
    answer decompressed when readable. In ``replay`` mode, nothing reaches the network
    nor runs: each call is answered from the tape (a JSON body matched by value),
    identical calls in the order recorded, then the last answer again; a call the tape
    does not hold fails with :class:`TapeMissError`, and so does any other outbound
    connection. ``secrets`` never reach the tape, and replay matches a call whatever
    secret it carries.

    :param path: the tape file
    :param mode: ``record`` or ``replay``
    :param secrets: values to keep off the tape (``Configuration.secret_values()``)
    :param daemon: the daemon recording, named in the tape's header
    """

    def __init__(
        self,
        path: str,
        mode: str,
        secrets: Sequence[str] = (),
        daemon: str | None = None,
    ) -> None:
        _tape.check(path, mode)
        self.path = path
        self.mode = mode
        self.secrets = list(secrets)
        self.daemon = daemon

    def start(self) -> "CallTape":
        """Start recording or replaying. A tape that cannot be replayed (not a JSON
        tape, another tape version, a call the SDK does not model) raises an
        ``OpenAEVError`` saying why."""
        _tape.start(self.path, self.mode, self.secrets, self.daemon)
        return self

    def stop(self) -> None:
        """Stop, and restore the real network and commands."""
        _tape.stop()

    def __enter__(self) -> "CallTape":
        return self.start()

    def __exit__(self, *_: Any) -> None:
        self.stop()


def lint_tape(path: str, secrets: Sequence[str] = ()) -> list[str]:
    """Returns each place of the tape at ``path`` holding what looks like a secret: a
    known secret value, or a secret-named header, parameter or JSON field whose value
    is not masked. Empty when the tape is clean."""
    return _tape.lint(path, secrets)
