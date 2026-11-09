"""Daemon data contracts shared by the daemon runtime and its callers."""

from dataclasses import dataclass

__all__ = ["DevOptions"]


@dataclass(frozen=True)
class DevOptions:
    """Command-line options common to every daemon started in dev mode (no platform).

    ``enabled`` is the ``--dev`` flag; the other fields only matter when it is set.
    ``out`` names where the calls the platform would have received are written
    (stdout when ``None``), ``record`` and ``replay`` name the tape of the daemon's
    outside calls, and ``help`` is ``--dev`` with ``-h`` or ``--help``. The injector and
    collector SDKs extend these options with their own.
    """

    enabled: bool = False
    out: str | None = None
    record: str | None = None
    replay: str | None = None
    help: bool = False
