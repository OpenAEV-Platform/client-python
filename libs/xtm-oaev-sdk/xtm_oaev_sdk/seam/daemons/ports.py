"""Daemon ports: the behaviour the public daemon runtime expects from the core."""

import argparse
import threading
from typing import Any, Callable, Protocol, runtime_checkable

from xtm_oaev_sdk.seam.common import BaseClient
from xtm_oaev_sdk.seam.configuration import ConfigurationProtocol
from xtm_oaev_sdk.seam.daemons.models import DevOptions

__all__ = ["DaemonRuntimePort", "HeartbeatPort"]


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
