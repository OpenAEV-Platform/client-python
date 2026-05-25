"""Signature lifecycle for OpenAEV injectors: compile pre, merge post, ship to backend."""

import logging
import os
import socket
import subprocess
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal

from pydantic import ValidationError

from pyoaev.exceptions import OpenAEVError
from pyoaev.signatures.models import (
    PostExecutionSignature,
    PreExecutionSignature,
    ToolOutput,
)

if TYPE_CHECKING:
    from pyoaev.client import OpenAEV


class SignatureManager:
    """End-to-end signature pipeline: compile, merge, transmit. One class, three jobs."""

    DEFAULT_MAX_PAYLOAD_SIZE = 1_048_576  # 1 MiB

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

    def compile_pre_execution_signatures(
        self,
        inject_config: dict[str, Any],
        category: Literal["network", "cloud", "external"],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Build pre-execution signature dicts off the inject config and category.

        Args:
            inject_config: The inject payload dict.
            category: One of 'network', 'cloud', 'external'.

        Returns:
            One dict for single-target, list of dicts for multi-target configs.

        Raises:
            ValueError: Unknown category or required fields missing.
        """
        now = self._utcnow()
        start_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        if category == "network":
            return self._compile_network_pre(inject_config, start_time)
        elif category == "cloud":
            return self._compile_cloud_pre(inject_config, start_time)
        elif category == "external":
            return self._compile_external_pre(inject_config, start_time)
        else:
            raise ValueError(f"Unknown category: {category!r}")

    def _compile_network_pre(
        self, config: dict[str, Any], start_time: str
    ) -> dict[str, Any] | list[dict[str, Any]]:
        ipv4 = self.resolve_container_ip()
        ipv6 = self._cached_ipv6

        assets = config.get("target_assets") or config.get("assets") or []
        if not assets:
            asset = config.get("asset")
            if asset:
                assets = [asset]

        if not assets:
            raise ValueError(
                "inject_config must contain 'target_assets', 'assets', or 'asset'"
            )

        results: list[dict[str, Any]] = []
        for asset in assets:
            sig = PreExecutionSignature(
                start_time=start_time,
                source_ipv4=ipv4,
                source_ipv6=ipv6,
                target_ipv4=asset["target_ipv4"],
                target_ipv6=asset.get("target_ipv6"),
                target_hostname=asset.get("target_hostname"),
            )
            results.append(sig.model_dump(mode="json", exclude_none=True))

        return results[0] if len(results) == 1 else results

    def _compile_cloud_pre(
        self, config: dict[str, Any], start_time: str
    ) -> dict[str, Any] | list[dict[str, Any]]:
        cloud_provider = config["cloud_provider"]
        cloud_account_id = config["cloud_account_id"]
        target_service = config.get("target_service")

        regions = config.get("regions") or []
        if not regions:
            region = config.get("cloud_region")
            if region:
                regions = [region]

        if not regions:
            raise ValueError("inject_config must contain 'regions' or 'cloud_region'")

        results: list[dict[str, Any]] = []
        for region in regions:
            sig = PreExecutionSignature(
                start_time=start_time,
                cloud_provider=cloud_provider,
                cloud_account_id=cloud_account_id,
                cloud_region=region,
                target_service=target_service,
            )
            results.append(sig.model_dump(mode="json", exclude_none=True))

        return results[0] if len(results) == 1 else results

    def _compile_external_pre(
        self, config: dict[str, Any], start_time: str
    ) -> dict[str, Any] | list[dict[str, Any]]:
        targets = config.get("targets") or []
        if not targets:
            query = config.get("query")
            if query is None:
                raise ValueError("inject_config must contain 'query'")
            targets = [
                {
                    "target_ipv4": config["target_ipv4"],
                    "target_hostname": config.get("target_hostname"),
                    "query": query,
                }
            ]

        results: list[dict[str, Any]] = []
        for target in targets:
            sig = PreExecutionSignature(
                start_time=start_time,
                target_ipv4=target["target_ipv4"],
                target_hostname=target.get("target_hostname"),
                query=target.get("query"),
            )
            results.append(sig.model_dump(mode="json", exclude_none=True))

        return results[0] if len(results) == 1 else results

    def compile_post_execution_signatures(
        self,
        pre_signatures: dict[str, Any] | list[dict[str, Any]],
        tool_output: dict[str, Any],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Merge pre-execution dicts with the tool's verdict into post-execution dicts.

        Args:
            pre_signatures: One pre-execution dict or a list of them.
            tool_output: Tool result with optional `error_info` / `timeout_info` / `status`.

        Returns:
            Same shape as `pre_signatures`, now carrying `end_time` and `execution_status`.
        """
        if isinstance(pre_signatures, list):
            return [self._merge_post(sig, tool_output) for sig in pre_signatures]
        return self._merge_post(pre_signatures, tool_output)

    def _merge_post(
        self, pre_sig: dict[str, Any], tool_output: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            tool = ToolOutput.model_validate(tool_output or {})
        except ValidationError as exc:
            raise OpenAEVError(
                error_message=f"Invalid tool_output: {exc}",
            ) from exc

        post = PostExecutionSignature.model_validate(pre_sig)
        now = self._utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        if tool.error_info and tool.error_info.exit_code != 0:
            post.execution_status = "failed"
            post.end_time = tool.error_info.crash_timestamp or now
        elif tool.timeout_info:
            post.execution_status = "timeout"
            post.end_time = now
            if tool.timeout_info.partial_results:
                post.partial_results = tool.timeout_info.partial_results
        elif tool.status == "partial":
            post.execution_status = "partial"
            post.end_time = now
        else:
            post.execution_status = "success"
            post.end_time = now

        merged = post.model_dump(mode="json", exclude_none=True)

        if tool.extra_signatures:
            merged.update(tool.extra_signatures)

        return merged

    def send_signatures(
        self,
        inject_id: str,
        phase: str,
        signatures: dict[str, Any],
    ) -> None:
        """Ship signatures to the callback endpoint via the Signature API manager.

        Delegates transport (retry, chunking, validation) to ``client.signature``.

        Args:
            inject_id: Inject UUID.
            phase: Execution phase.
            signatures: Full signatures dict, canonical or flat, both grouped on the fly.

        Raises:
            SignatureTransmissionError: Validation failed, 4xx hit, or retries exhausted.
        """
        self.client.signature.max_payload_size = self.max_payload_size
        self.client.signature.logger = self.logger
        self.client.signature.send_signatures(inject_id, phase, signatures)

    def resolve_container_ip(self) -> str:
        """Sniff the container's primary IPv4. Env var, hostname, then ``hostname -i``.

        Returns:
            The IPv4 string, or ``'unknown'`` with a single warning when all strategies fail.
        """
        if self._cached_ipv4:
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
