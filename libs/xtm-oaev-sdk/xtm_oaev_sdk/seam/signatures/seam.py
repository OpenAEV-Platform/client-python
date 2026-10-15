"""The signatures capability's inbound seam: the versioned I/O models.

The frozen boundary both sides of the signatures capability share:

- **input face** — what is handed to the injector to execute: the
  ``InjectorConfig`` family (one network target, or one cloud target row)
  and the ``ExecutionSignature`` (the execution instruction and its
  outcome fields).
- **tool result face** — what the injected tool reports back:
  ``ToolOutput`` and its ``ToolErrorInfo`` / ``ToolTimeoutInfo``.

Pure data: this module imports nothing from the capability. The
dependency rule holds — the port imports the seam, never the other way,
and this module is the only thing both sides may import.

Any modification to the JSON schema of a model in this module is a
breaking change for consumers and must bump :data:`SEAM_VERSION`.

The seam golden (``test/seam/test_seam_golden.py``) fingerprints every public
object of the seam, this module included, and fails on drift.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, model_validator

#: Version of the signatures inbound seam. Bump on any breaking contract change.
SEAM_VERSION = "1.0.0"


class ToolErrorInfo(BaseModel):
    """Crash report. Non-zero exit code and a timestamp if the tool left one behind."""

    model_config = ConfigDict(extra="allow")

    exit_code: int = 0
    crash_timestamp: str | None = None


class ToolTimeoutInfo(BaseModel):
    """Timeout report. Whatever partial loot was rescued before the kill signal."""

    model_config = ConfigDict(extra="allow")

    partial_results: list[str] = Field(default_factory=list)


class ToolOutput(BaseModel):
    """Whatever the tool spat out: status, error info, timeout info, or injector extras."""

    model_config = ConfigDict(extra="allow")

    status: str | None = None
    error_info: ToolErrorInfo | None = None
    timeout_info: ToolTimeoutInfo | None = None


class ExecutionSignature(BaseModel):
    """
    Execution signature data. Field set varies by category: network, cloud. Plus outcome, end_time, and any partial results.
    """

    model_config = ConfigDict(extra="allow")

    # Timing always emitted at call time.
    start_time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    )
    end_time: str | None = None
    partial_results: list[str] | None = None

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

    def post_execution_update(self, tool_output: ToolOutput, now: datetime) -> None:
        """Update timing and partial results from tool output."""
        self.end_time = now.strftime("%Y-%m-%dT%H:%M:%SZ")

        if tool_output.error_info and tool_output.error_info.crash_timestamp:
            self.end_time = tool_output.error_info.crash_timestamp

        if tool_output.timeout_info and tool_output.timeout_info.partial_results:
            self.partial_results = tool_output.timeout_info.partial_results


class NetworkInjectorConfig(BaseModel):
    """A single network target. Exactly one of ``target_ipv4``, ``target_ipv6``, or ``target_hostname``."""

    model_config = ConfigDict(extra="forbid")

    target_ipv4: str | None = None
    target_ipv6: str | None = None
    target_hostname: str | None = None

    @model_validator(mode="before")
    @classmethod
    def check_one(cls, data):
        """Ensure exactly one target identity field is provided."""
        assert (
            sum(
                value is not None
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


InjectorConfig = NetworkInjectorConfig | CloudInjectorConfig


__all__ = [
    "SEAM_VERSION",
    "ToolErrorInfo",
    "ToolTimeoutInfo",
    "ToolOutput",
    "ExecutionSignature",
    "NetworkInjectorConfig",
    "CloudInjectorConfig",
    "InjectorConfig",
]
