"""Pydantic schemas pinning every shape SignatureManager touches.

The seam models live in the architectural seam layer and are re-exported
here so this module keeps its historical surface:

- the inbound seam (the ``InjectorConfig`` family, ``ExecutionSignature``,
  and the ``ToolOutput`` family) in
  ``xtm_oaev_sdk.seam.signatures.seam`` (versioned ``SEAM_VERSION``);
- the observation / callback wire models (the port I/O contract) in
  ``xtm_oaev_sdk.seam.port_io.models`` (versioned
  ``PORT_IO_CONTRACT_VERSION``).

Only ``ExtraSignatureData`` and the target-builder helpers are defined here
— they are the port's own shapes, internal to the capability.
"""

import ipaddress
from typing import Any

from pydantic import BaseModel, Field, JsonValue
from xtm_oaev_sdk.seam.port_io.models import (
    ExecutionDetails,
    ExpectationSignatureGroup,
    SignatureCallbackPayload,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
)
from xtm_oaev_sdk.seam.signatures.seam import (
    CloudInjectorConfig,
    ExecutionSignature,
    InjectorConfig,
    NetworkInjectorConfig,
    ToolErrorInfo,
    ToolOutput,
    ToolTimeoutInfo,
)


class ExtraSignatureData(BaseModel):
    """Format for extra signatures added to the default signatures."""

    detection: dict[str, JsonValue] = Field(default_factory=dict)
    prevention: dict[str, JsonValue] = Field(default_factory=dict)
    vulnerability: dict[str, JsonValue] = Field(default_factory=dict)

    def get_extra(self, expectation_type: str) -> dict[str, JsonValue]:
        if expectation_type.lower() == "detection":
            return self.detection
        if expectation_type.lower() == "prevention":
            return self.prevention
        if expectation_type.lower() == "vulnerability":
            return self.vulnerability
        raise ValueError(
            f"Expectation type should be one of the available parameters: {list(self.model_fields.keys())}"
        )


# ---------------------------------------------------------------------------
# Builders. Cheap helpers to turn raw injector input into typed configs.
# ---------------------------------------------------------------------------


def _classify_network_target(value: str) -> NetworkInjectorConfig:
    """Decide whether ``value`` is an IPv4, IPv6, or hostname and wrap it."""
    try:
        addr = ipaddress.ip_address(value)
    except ValueError:
        return NetworkInjectorConfig(target_hostname=value)
    if isinstance(addr, ipaddress.IPv4Address):
        return NetworkInjectorConfig(target_ipv4=value)
    return NetworkInjectorConfig(target_ipv6=value)


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
    configs: list[NetworkInjectorConfig] = []
    for target in targets:
        if isinstance(target, NetworkInjectorConfig):
            configs.append(target)
        elif isinstance(target, dict):
            configs.append(NetworkInjectorConfig(**target))
        elif isinstance(target, str):
            configs.append(_classify_network_target(target))
        else:
            raise TypeError(f"unsupported network target type: {type(target).__name__}")
    return configs


__all__ = [
    "SignatureValue",
    "ExpectationSignatureGroup",
    "ExtraSignatureData",
    "SignatureTarget",
    "TargetSignatures",
    "SignaturePayload",
    "SignatureOutputStructure",
    "ExecutionDetails",
    "SignatureCallbackPayload",
    "ExecutionSignature",
    "ToolErrorInfo",
    "ToolTimeoutInfo",
    "ToolOutput",
    "NetworkInjectorConfig",
    "CloudInjectorConfig",
    "InjectorConfig",
    "build_network_configs",
]
