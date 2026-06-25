"""Signature lifecycle for OpenAEV injectors: compile pre, merge post, ship to backend."""

import logging
import os
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from pydantic import ValidationError

from xtm_oaev_sdk._core.errors import OpenAEVError
from xtm_oaev_sdk._core.signatures.models import (
    CloudInjectorConfig,
    ExecutionDetails,
    ExecutionSignature,
    ExpectationSignatureGroup,
    ExtraSignatureData,
    InjectorConfig,
    NetworkInjectorConfig,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
    ToolOutput,
)

__all__ = [
    "SignatureManager",
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
        return datetime.now(timezone.utc)

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
        if not configs:
            raise ValueError("build_execution_signatures requires at least one config")

        first_type = type(configs[0])
        for c in configs:
            if not isinstance(c, first_type):
                raise ValueError(
                    "build_execution_signatures does not mix injector config types; "
                    f"got {sorted({type(c).__name__ for c in configs})}"
                )

        start_time = self._utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
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
        base: dict[str, Any] = {"start_time": start_time}
        base.update(self._source_context(config))
        base.update(config.model_dump(exclude_none=True))
        return ExecutionSignature(**base)

    def _source_context(self, config: InjectorConfig) -> dict[str, Any]:
        """Return the source identity bits injected for the config's category.

        Only network signatures need the running container's source IPs;
        cloud rows have no source identity to carry.
        """
        if isinstance(config, NetworkInjectorConfig):
            return {
                "source_ipv4": self.resolve_container_ip(),
                "source_ipv6": self._cached_ipv6,
            }
        if isinstance(config, CloudInjectorConfig):
            return {}
        raise TypeError(f"unsupported injector config type: {type(config).__name__}")

    def post_execution_updates(
        self,
        execution_details: ExecutionDetails,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        tool_output: dict[str, Any],
    ) -> None:
        """
        Update both execution details and execution signatures according to tool output
        """
        try:
            tool_output = ToolOutput.model_validate(tool_output or {})
        except ValidationError as exc:
            raise OpenAEVError(
                error_message=f"Invalid tool_output: {exc}",
            ) from exc

        now = self._utcnow()

        execution_details.post_execution_update(tool_output, now)

        if isinstance(execution_signatures, list):
            for exec_sig in execution_signatures:
                exec_sig.post_execution_update(tool_output, now)
        else:
            execution_signatures.post_execution_update(tool_output, now)

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
        if not isinstance(execution_signatures, list):
            execution_signatures = [execution_signatures]
        if isinstance(targets_meta, dict):
            targets_meta = [targets_meta] * len(execution_signatures)

        targets = []
        for signature, target in zip(execution_signatures, targets_meta):
            signature_values = []
            for expectation_type in expectation_types:
                signature_data = signature.model_dump(exclude_none=True)
                signature_data.update(extra_signatures.get_extra(expectation_type))
                values = [
                    SignatureValue(signature_type=key, signature_value=value)
                    for key, value in signature_data.items()
                ]
                signature_values.append(
                    ExpectationSignatureGroup(
                        expectation_type=expectation_type,
                        values=values,
                    )
                )
            targets.append(
                TargetSignatures(
                    signature_target=SignatureTarget(
                        agent=target.agent_id,
                        asset=target.asset_id,
                        asset_group=target.asset_group_id,
                    ),
                    signature_values=signature_values,
                )
            )

        return SignaturePayload(targets=targets).model_dump()

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
        sig_output = SignatureOutputStructure(signatures=SignaturePayload(**signatures))

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

        env_ip = os.environ.get("CONTAINER_IP")
        if env_ip:
            self._cached_ipv4 = env_ip
            self._resolve_ipv6()
            return env_ip

        try:
            ip = socket.gethostbyname(socket.gethostname())
            if ip and ip != "127.0.0.1":
                self._cached_ipv4 = ip
                self._resolve_ipv6()
                return ip
        except (socket.gaierror, OSError):
            pass

        try:
            result = subprocess.run(
                ["hostname", "-i"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                ip = result.stdout.strip().split()[0]
                if ip and ip != "127.0.0.1":
                    self._cached_ipv4 = ip
                    self._resolve_ipv6()
                    return ip
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            pass

        self.logger.warning("Could not resolve container IP; returning 'unknown'")
        self._cached_ipv4 = "unknown"
        return "unknown"

    def _resolve_ipv6(self) -> None:
        """Best-effort IPv6 sniff. Silent on failure, no exceptions escape."""
        try:
            infos = socket.getaddrinfo(
                socket.gethostname(), None, socket.AF_INET6, socket.SOCK_STREAM
            )
            for info in infos:
                addr = info[4][0]
                if (
                    isinstance(addr, str)
                    and addr
                    and not addr.startswith("::1")
                    and not addr.startswith("fe80")
                ):
                    self._cached_ipv6 = addr
                    return
        except (socket.gaierror, OSError):
            pass
