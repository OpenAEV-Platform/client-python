"""Daemon ports: the behaviour the public daemon runtime expects from the core."""

import argparse
import threading
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    Protocol,
    Sequence,
    runtime_checkable,
)

from xtm_oaev_sdk.seam.common import BaseClient
from xtm_oaev_sdk.seam.configuration import ConfigurationProtocol
from xtm_oaev_sdk.seam.daemons.models import DevOptions

__all__ = ["DaemonRuntimePort", "DevSinkFactoryPort", "DevSinkPort", "HeartbeatPort"]


@runtime_checkable
class DaemonRuntimePort(Protocol):
    """Runs the shared lifecycle of collector and injector daemons."""

    def resolve_log_level(self, configuration: ConfigurationProtocol) -> str:
        """Log level, from the generic or the legacy collector/injector keys."""

    def resolve_name(self, configuration: ConfigurationProtocol) -> str:
        """Daemon name, from the generic or the legacy collector/injector keys."""

    def resolve_id(self, configuration: ConfigurationProtocol) -> Any:
        """Daemon id, from ``id``, ``collector_id`` or ``injector_id``."""

    def invoke_callback(
        self, callback: Callable[..., Any] | None, daemon: Any, logger: Any
    ) -> None:
        """Call the callback (injecting the daemon as ``collector`` when asked
        for), logging and swallowing any error."""

    def dump_config_schema_requested(self) -> bool:
        """Whether the daemon was started with ``--dump-config-schema``. Flags the
        daemon does not own are ignored."""

    def dev_argument_parser(
        self, description: str | None = None, epilog: str | None = None
    ) -> argparse.ArgumentParser:
        """A new parser holding the dev options common to every daemon, which an
        injector or collector SDK extends with its own option group. It reads options
        only under their full name and never prints help nor exits on its own."""

    def dev_options(self, argv: list[str] | None = None) -> DevOptions:
        """Common dev options read from ``argv`` (the process arguments when ``None``).
        Flags the daemon does not own are ignored."""

    def dev_help(self) -> str:
        """Help of the common dev options: each option and what it is for."""

    def dump_config_schema(self, configuration: ConfigurationProtocol) -> None:
        """Print the configuration JSON schema."""

    def ensure_callback(self, callback: Callable[..., Any] | None) -> None:
        """Raise when the daemon has no callback to run."""

    def default_api_client(self) -> BaseClient:
        """The API client used when none is injected: none, the SDK refuses."""


@runtime_checkable
class HeartbeatPort(Protocol):
    """Keeps a daemon registered on the platform."""

    def tenant_of(self, api: Any) -> Any:
        """Tenant the API client is scoped to, if any."""

    def tenant_meta(self, tenant_id: Any) -> dict[str, Any]:
        """Log metadata identifying the tenant."""

    def ping(
        self,
        api: Any,
        config: Any,
        ping_type: str,
        logger: Any,
        exit_event: threading.Event,
    ) -> None:
        """Register the daemon every 40 seconds until ``exit_event`` is set."""


@runtime_checkable
class DevSinkPort(Protocol):
    """Where a daemon in dev mode writes the calls the platform would have received.

    ``calls`` holds each call as recorded, unredacted, for the run to read.
    """

    calls: list[dict[str, Any]]

    def record(self, method: str, path: str, body: Any) -> None:
        """Check ``body`` against the payload the platform accepts on ``path``, then
        write the call, redacted. A body the platform would reject raises an
        ``OpenAEVHttpError`` with ``response_code`` 400, and nothing is written."""

    def redact(self, value: Any) -> Any:
        """``value`` with every secret replaced by ``***``, structure kept. JSON text
        is redacted as JSON, so escaped secrets go too."""

    def wait_for(
        self, condition: Callable[[list[dict[str, Any]]], bool], timeout: float
    ) -> bool:
        """Wait until ``condition`` holds for the calls recorded so far, whatever
        thread records them; ``False`` when ``timeout`` seconds pass first."""

    def note(self, text: str) -> None:
        """Write ``dev: <text>`` on stderr, redacted."""

    def refuse(self, reason: str) -> int:
        """Say why the run is refused on stderr, redacted, and return exit code 2."""

    def close(self) -> None:
        """Write the calls a last time: to the output file, or once to stdout (or
        stderr) when there is none."""


@runtime_checkable
class DevSinkFactoryPort(Protocol):
    """Opens dev sinks and finds the secrets they must redact."""

    def open(
        self,
        out: str | None,
        secrets: Sequence[str],
        keep: Iterable[str],
        to_stderr: bool,
    ) -> DevSinkPort:
        """A sink writing one JSON list to ``out`` (rewritten after each call), or
        to stdout (stderr when ``to_stderr``) on close. ``secrets`` are redacted from
        every value but those of the ``keep`` keys."""

    def environment_secrets(self, environ: Mapping[str, str] | None) -> list[str]:
        """Values of the environment variables (``os.environ`` when ``None``) whose
        name says they hold a secret."""
