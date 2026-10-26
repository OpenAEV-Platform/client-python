"""Signature lifecycle for OpenAEV injectors: compile pre, merge post, ship to backend."""

import logging
import os
import socket
import subprocess
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from pyoaev.exceptions import OpenAEVError
from pyoaev.signatures.models import (
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
from pyoaev.signatures.types import SignatureTypes

if TYPE_CHECKING:
    from pyoaev.client import OpenAEV

logger = logging.getLogger(__name__)

# ExecutionSignature fields whose name differs from the signature type the platform
# and collectors expect. The cloud fields already use the canonical names.
EXECUTION_SIGNATURE_TYPES = {
    "start_time": SignatureTypes.SIG_TYPE_START_DATE.value,
    "end_time": SignatureTypes.SIG_TYPE_END_DATE.value,
    "source_ipv4": SignatureTypes.SIG_TYPE_SOURCE_IPV4_ADDRESS.value,
    "source_ipv6": SignatureTypes.SIG_TYPE_SOURCE_IPV6_ADDRESS.value,
    "target_ipv4": SignatureTypes.SIG_TYPE_TARGET_IPV4_ADDRESS.value,
    "target_ipv6": SignatureTypes.SIG_TYPE_TARGET_IPV6_ADDRESS.value,
    "target_hostname": SignatureTypes.SIG_TYPE_TARGET_HOSTNAME_ADDRESS.value,
}
SIGNATURE_TYPE_VALUES = frozenset(
    signature_type.value for signature_type in SignatureTypes
)


class SignatureManager:
    """End-to-end signature pipeline: compile, merge, transmit. One class, three jobs."""

    DEFAULT_MAX_PAYLOAD_SIZE = 5_242_880  # 5 MiB

    def __init__(
        self,
        client: "OpenAEV",
        logger: logging.Logger | None = None,
        max_payload_size: int = DEFAULT_MAX_PAYLOAD_SIZE,
    ) -> None:
        self.client = client
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
             and emit JSON-ready output stripped of ``None``\\ s.
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
            A payload dict ready for send_signatures. Signature types are the canonical
            ``SignatureTypes`` values (e.g. ``start_time`` is sent as ``start_date``);
            keys that are not a ``SignatureTypes`` value, and non-scalar values, are
            left out because collectors cannot parse them.
        """
        if not isinstance(execution_signatures, list):
            execution_signatures = [execution_signatures]
        if isinstance(targets_meta, dict):
            targets_meta = [targets_meta] * len(execution_signatures)

        skipped: set[str] = set()
        targets = []
        for signature, target in zip(execution_signatures, targets_meta):
            signature_values = []
            for expectation_type in expectation_types:
                signature_data = SignatureManager._canonical_signatures(
                    signature.model_dump(exclude_none=True), skipped
                )
                signature_data.update(
                    SignatureManager._canonical_signatures(
                        extra_signatures.get_extra(expectation_type), skipped
                    )
                )
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

        if skipped:
            logger.warning(
                "Signatures left out of the payload, not a known signature type "
                "or not a single value: %s",
                ", ".join(sorted(skipped)),
            )
        return SignaturePayload(targets=targets).model_dump()

    @staticmethod
    def _canonical_signatures(
        signature_data: dict[str, Any], skipped: set[str]
    ) -> dict[str, Any]:
        """Rename signature keys to their ``SignatureTypes`` value and drop the rest.

        Collectors parse each signature as a ``SignatureTypes`` and a string, and the
        platform discards empty and non-scalar values, so unknown keys and ``None``,
        list or dict values are added to ``skipped`` instead.
        """
        canonical = {}
        for key, value in signature_data.items():
            signature_type = EXECUTION_SIGNATURE_TYPES.get(key, key)
            if (
                signature_type not in SIGNATURE_TYPE_VALUES
                or value is None
                or isinstance(value, (list, dict))
            ):
                skipped.add(key)
                continue
            canonical[signature_type] = value
        return canonical

    def send_signatures(
        self,
        inject_id: str,
        execution_details: ExecutionDetails,
        signatures: dict[str, Any],
    ) -> None:
        """Ship signatures to the callback endpoint via the Signature API manager.

        Constructs typed ``SignatureOutputStructure`` and ``ExecutionDetails``
        models, then delegates transport (retry, envelope splitting, validation)
        to ``client.signature``.

        Args:
            inject_id: Inject UUID.
            execution_details: execution-related metadata as an ExecutionDetails object
            signatures: Full signatures dict with a ``targets`` list.

        Raises:
            SignatureTransmissionError: Validation failed, 4xx hit, or retries exhausted.
        """
        sig_output = SignatureOutputStructure(
            expectation_signatures=SignaturePayload(**signatures)
        )

        self.client.signature.send_signatures(
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
