"""Signature ports.

``SignatureTransportProtocol`` is the driven port the signature manager ships
signatures through (implemented by API clients); ``SignatureManagerProtocol``
is the consumer-facing contract of signature managers. The other protocols
are the ports the public adapters delegate to; the core implements them.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Protocol, runtime_checkable

from xtm_oaev_sdk.seam.port_io import ExecutionDetails, SignatureOutputStructure
from xtm_oaev_sdk.seam.signatures.models import ExtraSignatureData
from xtm_oaev_sdk.seam.signatures.seam import (
    ExecutionSignature,
    InjectorConfig,
    NetworkInjectorConfig,
)

__all__ = [
    "ContainerAddressPort",
    "MarkerPort",
    "NetworkTargetsPort",
    "SignatureEnginePort",
    "SignatureManagerProtocol",
    "SignatureTransportProtocol",
]


@runtime_checkable
class SignatureTransportProtocol(Protocol):
    """Transport contract for signature delivery.

    pyoaev implements this via its Signature API manager.
    The SDK only knows this interface, never the concrete client.
    """

    def send_signatures(
        self,
        inject_id: str,
        sig_output: SignatureOutputStructure,
        execution_details: ExecutionDetails,
        *,
        max_payload_size: int,
        logger: logging.Logger,
    ) -> None:
        """Transmit signatures to the platform callback endpoint."""
        ...


@runtime_checkable
class SignatureManagerProtocol(Protocol):
    """Behavioral contract for the signature lifecycle manager.

    Covers the full compile → merge → transmit pipeline.
    """

    def build_execution_signatures(
        self,
        config: InjectorConfig | list[InjectorConfig],
    ) -> ExecutionSignature | list[ExecutionSignature]:
        """Build pre-execution signatures from injector configs."""
        ...

    def post_execution_updates(
        self,
        execution_details: ExecutionDetails,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        tool_output: dict[str, Any],
    ) -> None:
        """Update execution metadata after tool completion."""
        ...

    def send_signatures(
        self,
        inject_id: str,
        execution_details: ExecutionDetails,
        signatures: dict[str, Any],
    ) -> None:
        """Ship signatures to the callback endpoint."""
        ...

    def resolve_container_ip(self) -> str:
        """Resolve the container's primary IPv4 address."""
        ...


@runtime_checkable
class SignatureEnginePort(Protocol):
    """Compiles, merges and packages execution signatures."""

    def now(self) -> datetime:
        """Current UTC time."""

    def validate_configs(self, configs: list[InjectorConfig]) -> None:
        """Raise unless there is at least one config, all of the same type."""

    def format_start_time(self, now: datetime) -> str:
        """Start time of the execution signatures."""

    def source_context(
        self,
        config: InjectorConfig,
        source_ipv4: Callable[[], str],
        source_ipv6: Callable[[], str | None],
    ) -> dict[str, Any]:
        """Source identity fields of a config's signature."""

    def build_signature(
        self, config: InjectorConfig, start_time: str, source_context: dict[str, Any]
    ) -> ExecutionSignature:
        """Pre-execution signature of one config."""

    def apply_tool_output(
        self,
        execution_details: ExecutionDetails,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        tool_output: dict[str, Any],
        now: Callable[[], datetime],
    ) -> None:
        """Merge the validated tool output into details and signatures, at the
        time ``now`` returns once the output is valid."""

    def build_payload(
        self,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        targets_meta: Any | list[Any],
        expectation_types: list[str],
        extra_signatures: ExtraSignatureData,
    ) -> dict[str, Any]:
        """Wire payload of the signatures, per target and expectation type."""

    def output_structure(self, signatures: dict[str, Any]) -> SignatureOutputStructure:
        """Structure shipped through the transport."""


@runtime_checkable
class ContainerAddressPort(Protocol):
    """Resolves the addresses of the container running the injector."""

    def resolve_ipv4(self, logger: logging.Logger) -> str | None:
        """Container IPv4 (env, socket, ``hostname -i``), None when unresolved."""

    def resolve_ipv6(self) -> str | None:
        """Container global IPv6, None when there is none."""


@runtime_checkable
class NetworkTargetsPort(Protocol):
    """Turns raw injector targets into network injector configs."""

    def build_network_configs(
        self, targets: list[str | dict[str, Any] | NetworkInjectorConfig]
    ) -> list[NetworkInjectorConfig]:
        """One config per target, order preserved."""


@runtime_checkable
class MarkerPort(Protocol):
    """Derives the per-inject canary marker of AI injects."""

    def build_marker(self, inject_id: str, agent_id: str = "") -> str:
        """Deterministic marker of an inject (and agent)."""
