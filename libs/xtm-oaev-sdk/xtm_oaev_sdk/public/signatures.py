"""Signature adapters: the signature manager and the target/marker helpers.

Each adapter speaks the signatures seam types and delegates to the core
implementation of its port; signatures are shipped through an injected
``SignatureTransportProtocol``.
"""

import logging
from datetime import datetime
from typing import Any

from xtm_oaev_sdk._core.signatures import (
    ContainerAddressResolver,
    MarkerBuilder,
    NetworkTargets,
    SignatureEngine,
)
from xtm_oaev_sdk.seam.port_io import ExecutionDetails
from xtm_oaev_sdk.seam.signatures import (
    CloudInjectorConfig,
    ContainerAddressPort,
    ExecutionSignature,
    ExtraSignatureData,
    InjectorConfig,
    MarkerPort,
    MatchTypes,
    NetworkInjectorConfig,
    NetworkTargetsPort,
    SignatureEnginePort,
    SignatureManagerProtocol,
    SignatureMatch,
    SignatureTransportProtocol,
    SignatureType,
    SignatureTypes,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
)

__all__ = [
    "CloudInjectorConfig",
    "ExecutionSignature",
    "ExtraSignatureData",
    "InjectorConfig",
    "MatchTypes",
    "NetworkInjectorConfig",
    "SignatureManager",
    "SignatureManagerProtocol",
    "SignatureMatch",
    "SignatureTransportProtocol",
    "SignatureType",
    "SignatureTypes",
    "ToolErrorInfo",
    "ToolOutput",
    "ToolTimeoutInfo",
    "build_marker",
    "build_network_configs",
]

_engine: SignatureEnginePort = SignatureEngine()
_addresses: ContainerAddressPort = ContainerAddressResolver()
_targets: NetworkTargetsPort = NetworkTargets()
_marker: MarkerPort = MarkerBuilder()


class SignatureManager:
    """End-to-end signature pipeline: compile, merge, transmit. One class, three jobs."""

    DEFAULT_MAX_PAYLOAD_SIZE = 5_242_880  # 5 MiB

    def __init__(
        self,
        transport: SignatureTransportProtocol,
        logger: logging.Logger | None = None,
        max_payload_size: int = DEFAULT_MAX_PAYLOAD_SIZE,
    ) -> None:
        """Initialize manager with a transport implementation for signature delivery."""
        self.transport = transport
        self.logger = logger or logging.getLogger(__name__)
        self.max_payload_size = max_payload_size
        self._cached_ipv4: str | None = None
        self._cached_ipv6: str | None = None

    def _utcnow(self) -> datetime:
        """Current UTC time. Carved out so tests can pin the clock."""
        return _engine.now()

    def build_execution_signatures(
        self,
        config: InjectorConfig | list[InjectorConfig],
    ) -> ExecutionSignature | list[ExecutionSignature]:
        """Build pre-execution signature dicts from one or more typed injector configs.

        The category is carried by the config type itself
        (:class:`NetworkInjectorConfig`, :class:`CloudInjectorConfig`),
        so no separate ``category`` flag is needed.

        Args:
            config: A single injector config or a homogeneous list of them.
                Multi-target injects must be expressed as a list.

        Returns:
            One ExecutionSignature object when a single config is given,
            otherwise a list of ExecutionSignature in input order.

        Raises:
            ValueError: Empty list, or mixed config types in a single call.
            TypeError: Unknown injector config type.
        """
        configs = list(config) if isinstance(config, list) else [config]
        _engine.validate_configs(configs)
        start_time = _engine.format_start_time(self._utcnow())
        results = [self._build_one(cfg, start_time) for cfg in configs]
        return results[0] if len(results) == 1 else results

    def _build_one(self, config: InjectorConfig, start_time: str) -> ExecutionSignature:
        """Project a single injector config into a flat pre-execution signature dict.

        Common pipeline for every category:
          1. Seed the base dict with ``start_time`` and category-specific context
             (network gets resolved source IPs; cloud add nothing).
          2. Layer the config's own fields on top.
          3. Run it through :class:`ExecutionSignature` for validation
             and emit JSON-ready output stripped of ``None``\\s.
        """
        return _engine.build_signature(config, start_time, self._source_context(config))

    def _source_context(self, config: InjectorConfig) -> dict[str, Any]:
        """Return the source identity bits injected for the config's category.

        Only network signatures need the running container's source IPs;
        cloud rows have no source identity to carry.
        """
        return _engine.source_context(
            config, self.resolve_container_ip, lambda: self._cached_ipv6
        )

    def post_execution_updates(
        self,
        execution_details: ExecutionDetails,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        tool_output: dict[str, Any],
    ) -> None:
        """
        Update both execution details and execution signatures according to tool output
        """
        _engine.apply_tool_output(
            execution_details, execution_signatures, tool_output, self._utcnow
        )

    @staticmethod
    def build_payload(
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        targets_meta: Any | list[Any],
        expectation_types: list[str],
        extra_signatures: ExtraSignatureData = ExtraSignatureData(),
    ) -> dict[str, Any]:
        """Build the nested wire payload from flat post-execution signatures.

        Bridges the gap between compile_post_execution_signatures output (flat dicts)
        and send_signatures input (nested wire format).

        Args:
            execution_signatures: A single post-execution ExecutionSignature or a list (multi-targets).
            targets_meta: Target metadata dict(s) with keys like agent, asset, asset_group.
            expectation_types: The 1+ expectation type labels (e.g. ['DETECTION', 'PREVENTION']).
            extra_signatures: Optional mapping of expectation types to additional signature fields that will be merged
            into the base post_signatures.

        Returns:
            A payload dict ready for send_signatures.
        """
        return _engine.build_payload(
            execution_signatures, targets_meta, expectation_types, extra_signatures
        )

    def send_signatures(
        self,
        inject_id: str,
        execution_details: ExecutionDetails,
        signatures: dict[str, Any],
    ) -> None:
        """Ship signatures to the callback endpoint via the configured transport.

        Constructs typed ``SignatureOutputStructure`` and ``ExecutionDetails``
        models, then delegates transport (retry, envelope splitting, validation)
        to the configured signature transport.

        Args:
            inject_id: Inject UUID.
            execution_details: execution-related metadata as an ExecutionDetails object
            signatures: Full signatures dict with a ``targets`` list.

        Raises:
            SignatureTransmissionError: Validation failed, 4xx hit, or retries exhausted.
        """
        sig_output = _engine.output_structure(signatures)
        self.transport.send_signatures(
            inject_id,
            sig_output,
            execution_details,
            max_payload_size=self.max_payload_size,
            logger=self.logger,
        )

    def resolve_container_ip(self) -> str:
        """Sniff the container's primary IPv4. Env var, hostname, then ``hostname -i``.

        Returns:
            The IPv4 string, or ``'unknown'`` with a warning when all strategies fail.
        """
        if self._cached_ipv4 and self._cached_ipv4 != "unknown":
            return self._cached_ipv4

        ip = _addresses.resolve_ipv4(self.logger)
        if ip is None:
            self._cached_ipv4 = "unknown"
            return "unknown"
        self._cached_ipv4 = ip
        self._resolve_ipv6()
        return ip

    def _resolve_ipv6(self) -> None:
        """Best-effort IPv6 sniff. Silent on failure, no exceptions escape."""
        addr = _addresses.resolve_ipv6()
        if addr:
            self._cached_ipv6 = addr


def build_network_configs(
    targets: list[str | dict[str, Any] | NetworkInjectorConfig],
) -> list[NetworkInjectorConfig]:
    """Forge a list of `NetworkInjectorConfig` from a heterogeneous target list.

    Each item is one distinct asset. Accepted shapes:

    - `NetworkInjectorConfig`: passed through unchanged.
    - `dict`: validated against :class:`NetworkInjectorConfig`.
    - `str`: auto-classified into IPv4 / IPv6 / hostname.

    Args:
        targets: Raw target list straight out of the injector.

    Returns:
        One `NetworkInjectorConfig` per input target, order preserved.

    Raises:
        TypeError: An item is not one of the accepted shapes.
        ValidationError: A dict item fails the one-identity invariant.
    """
    return _targets.build_network_configs(targets)


def build_marker(inject_id: str, agent_id: str = "") -> str:
    return _marker.build_marker(inject_id, agent_id)
