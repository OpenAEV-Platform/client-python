"""Call tape port: the behaviour the public call tape expects from the core."""

from typing import Protocol, Sequence, runtime_checkable

__all__ = ["CallTapePort"]


@runtime_checkable
class CallTapePort(Protocol):
    """Records the process's outside calls (HTTP, commands) to a tape, or answers them
    from it. One tape runs at a time."""

    def check(self, path: str, mode: str) -> None:
        """Raise ``ValueError`` when ``mode`` is neither ``record`` nor ``replay``."""

    def start(
        self, path: str, mode: str, secrets: Sequence[str], daemon: str | None
    ) -> None:
        """Start recording to ``path`` (rewritten whole after each call), or replaying
        from it; under replay, any other outbound connection fails closed. ``secrets``
        never reach the tape, and replay matches a call whatever secret it carries.
        A tape that cannot be replayed raises an ``OpenAEVError`` saying why."""

    def stop(self) -> None:
        """Stop the tape and restore the real network and commands."""

    def lint(self, path: str, secrets: Sequence[str]) -> list[str]:
        """Each place of the tape at ``path`` holding what looks like a secret: a
        known secret value, or a secret-named header, parameter or field whose value is
        not masked. Empty when the tape is clean."""
