"""Pydantic schemas pinning every shape SignatureManager touches."""

import ipaddress
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    field_validator,
    model_validator,
)

from pyoaev.signatures.types import ExpectationType


class SignatureValue(BaseModel):
    """One signature observation: a type and the value it carries."""

    model_config = ConfigDict(extra="allow")

    signature_type: str
    signature_value: JsonValue


class ExpectationSignatureGroup(BaseModel):
    """Values bound to a single expectation type (DETECTION, PREVENTION, ...)."""

    model_config = ConfigDict(extra="allow")

    expectation_type: str
    values: list[SignatureValue]

    @field_validator("expectation_type", mode="after")
    @classmethod
    def is_expectation_type(cls, value: str) -> str:
        ExpectationType(value.upper())
        return value


class ExtraSignatureData(BaseModel):
    """Format for extra signatures added to the default signatures"""

    detection: dict[str, JsonValue] | None = Field(default_factory=dict)
    prevention: dict[str, JsonValue] | None = Field(default_factory=dict)
    vulnerability: dict[str, JsonValue] | None = Field(default_factory=dict)

    def get_extra(self, expectation_type: str):
        if expectation_type.lower() == "detection":
            return self.detection
        if expectation_type.lower() == "prevention":
            return self.prevention
        if expectation_type.lower() == "vulnerability":
            return self.vulnerability
        raise ValueError(
            f"Expectation type should be one of the available parameters: {list(self.model_fields.keys())}"
        )


class SignatureTarget(BaseModel):
    """Target identity on the wire."""

    model_config = ConfigDict(extra="forbid")

    agent: str | None = None
    asset: str | None = None
    asset_group: str | None = None


class TargetSignatures(BaseModel):
    """A target plus everything observed about it, grouped by expectation."""

    model_config = ConfigDict(extra="allow")

    signature_target: SignatureTarget
    signature_values: list[ExpectationSignatureGroup]


class SignaturePayload(BaseModel):
    """Inner ``signatures`` body: a list of targets, nothing else."""

    model_config = ConfigDict(extra="allow")

    targets: list[TargetSignatures]


class SignatureCallbackPayload(BaseModel):
    """Outer POST envelope. Pure ``{signatures}`` when unchunked, plus chunk fields when split."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    expectation_signature: SignaturePayload
    phase: str | None = None
    chunk_index: int | None = None
    total_chunks: int | None = None


class PreExecutionSignature(BaseModel):
    """Pre-execution data dump. Field set varies by category: network, cloud, external."""

    model_config = ConfigDict(extra="allow")

    # Timing always emitted at call time.
    start_time: str | None = None

    # Network identity
    source_ipv4: str | None = None
    source_ipv6: str | None = None
    target_ipv4: str | None = None
    target_ipv6: str | None = None
    target_hostname: str | None = None

    # Cloud identity
    cloud_provider: str | None = None
    cloud_account_id: str | None = None
    cloud_region: str | None = None
    target_service: str | None = None

    # External
    query: str | None = None


class PostExecutionSignature(PreExecutionSignature):
    """Post-execution view: pre-execution fields plus outcome, end_time, and any partial results."""

    end_time: str | None = None
    execution_status: str | None = None
    partial_results: list[str] | None = None


class ToolErrorInfo(BaseModel):
    """Crash report. Non-zero exit code and a timestamp if the tool left one behind."""

    model_config = ConfigDict(extra="allow")

    exit_code: int = 0
    crash_timestamp: str | None = None


class ToolTimeoutInfo(BaseModel):
    """Timeout report. Whatever partial loot was rescued before the kill signal."""

    model_config = ConfigDict(extra="allow")

    partial_results: list[str] = []


class ToolOutput(BaseModel):
    """Whatever the tool spat out: status, error info, timeout info, or injector extras."""

    model_config = ConfigDict(extra="allow")

    status: str | None = None
    error_info: ToolErrorInfo | None = None
    timeout_info: ToolTimeoutInfo | None = None


class NetworkInjectorConfig(BaseModel):
    """A single network target. Exactly one of ``target_ipv4``, ``target_ipv6``, or ``target_hostname``."""

    model_config = ConfigDict(extra="forbid")

    target_ipv4: str | None = None
    target_ipv6: str | None = None
    target_hostname: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_one(cls, data):
        assert (
            sum(
                value != None
                for key, value in data.items()
                if key in ["target_ipv4", "target_ipv6", "target_hostname"]
            )
            == 1
        )
        return data


class CloudInjectorConfig(BaseModel):
    """A single cloud target row. One config per region; fan out by passing a list."""

    model_config = ConfigDict(extra="forbid")

    cloud_provider: str
    cloud_account_id: str
    cloud_region: str
    target_service: str | None = None


class ExternalInjectorConfig(BaseModel):
    """A single external scan target (e.g. Shodan): a query against an asset."""

    model_config = ConfigDict(extra="forbid")

    query: str
    target_ipv4: str | None = None
    target_hostname: str | None = None


InjectorConfig = NetworkInjectorConfig | CloudInjectorConfig | ExternalInjectorConfig


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
    "SignatureTarget",
    "TargetSignatures",
    "SignaturePayload",
    "SignatureCallbackPayload",
    "PreExecutionSignature",
    "PostExecutionSignature",
    "ToolErrorInfo",
    "ToolTimeoutInfo",
    "ToolOutput",
    "NetworkInjectorConfig",
    "CloudInjectorConfig",
    "ExternalInjectorConfig",
    "InjectorConfig",
    "build_network_configs",
]
