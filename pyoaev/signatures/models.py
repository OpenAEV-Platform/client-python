"""Pydantic schemas pinning every shape SignatureManager touches."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class SignatureValue(BaseModel):
    """One signature observation: a type and the value it carries."""

    model_config = ConfigDict(extra="allow")

    signature_type: str
    signature_value: str


class ExpectationSignatureGroup(BaseModel):
    """Values bound to a single expectation type (DETECTION, PREVENTION, ...)."""

    model_config = ConfigDict(extra="allow")

    expectation_type: str
    values: list[SignatureValue]


class SignatureTarget(BaseModel):
    """Target identity on the wire. Three fields, all mandatory, no exceptions."""

    model_config = ConfigDict(extra="allow")

    agent: str
    asset: str
    asset_group: str


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
    extra_signatures: dict[str, Any] | None = None


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
]
