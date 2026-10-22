"""The port I/O wire schema — the seam-owned models crossing the SDK↔platform boundary.

These pydantic models — together with the three wire-vocabulary enums
they serialise (``SignatureExpectationType``, ``ExecutionStatus``,
``InjectExecutionActions``) — are the exact JSON shapes transmitted between
the SDK's transport port (``SignatureTransportProtocol``) and the
platform's callback endpoint.  The seam is their **owner**: the capability's
port (``_core/signatures``) imports and re-exports from here, never the
reverse, so the two sides of the boundary can evolve independently.

- contract unchanged + port (internal) changes  →  no breaking change
- contract unchanged + adapter (public) changes  →  retrocompat holds
- contract changes                               →  **breaking change**

Any modification to the JSON schema of a model in this module is a breaking
change for consumers and must bump :data:`PORT_IO_CONTRACT_VERSION`.

The seam golden (``test/seam/test_seam_golden.py``) fingerprints every public
object of the seam, this module included, and fails on drift.

The module is **closed**: at runtime it imports only the standard library and
pydantic. ``ToolOutput`` (from the signatures inbound seam,
``seam/signatures/seam.py``) is referenced for type checking only, by
``ExecutionDetails.post_execution_update``: importing it at runtime would run
``seam/signatures/__init__`` and, through it, ``_core`` — an import cycle back
into this module. The wire contract therefore has no hidden dependency on
internal layout.
"""

import math
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    TypeAdapter,
    computed_field,
    field_validator,
)

if TYPE_CHECKING:
    from xtm_oaev_sdk.seam.signatures.seam import ToolOutput

#: Version of the port I/O wire schema. Bump on any breaking contract change.
PORT_IO_CONTRACT_VERSION = "1.0.0"

# --- Wire vocabulary -----------------------------------------------------------
# The three enums that appear in the JSON contract below. They live here, in
# the seam, because they are part of the wire schema; the internal
# implementation imports them from here (``_core/signatures/types``
# re-exports them for its historical import paths).


class SignatureExpectationType(str, Enum):
    """Expectation categories for a signature."""

    DETECTION = "DETECTION"
    PREVENTION = "PREVENTION"
    VULNERABILITY = "VULNERABILITY"


class ExecutionStatus(str, Enum):
    """Outcome status of a single inject tool execution.

    A ``str`` enum so it serialises to its string form in callback payloads.
    Mirrors the platform's execution-status taxonomy label-for-label.
    """

    EXECUTED = "EXECUTED"
    EXECUTED_WITH_CLEANUP_FAILURE = "EXECUTED_WITH_CLEANUP_FAILURE"
    WARNING = "WARNING"
    ACCESS_DENIED = "ACCESS_DENIED"
    ERROR = "ERROR"
    COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
    COMMAND_CANNOT_BE_EXECUTED = "COMMAND_CANNOT_BE_EXECUTED"
    PREREQUISITE_FAILED = "PREREQUISITE_FAILED"
    INVALID_USAGE = "INVALID_USAGE"
    TIMEOUT = "TIMEOUT"
    INTERRUPTED = "INTERRUPTED"
    ASSET_AGENTLESS = "ASSET_AGENTLESS"
    AGENT_INACTIVE = "AGENT_INACTIVE"
    AGENT_OVERLOADED = "AGENT_OVERLOADED"
    INFO = "INFO"
    PARTIAL = "PARTIAL"
    MAYBE_PREVENTED = "MAYBE_PREVENTED"
    MAYBE_PARTIAL_PREVENTED = "MAYBE_PARTIAL_PREVENTED"


class InjectExecutionActions(str, Enum):
    """Execution action phases used by injection signatures."""

    PREREQUISITE_CHECK = "prerequisite_check"
    PREREQUISITE_EXECUTION = "prerequisite_execution"
    CLEANUP_EXECUTION = "cleanup_execution"
    COMMAND_EXECUTION = "command_execution"
    DNS_RESOLUTION = "dns_resolution"
    FILE_EXECUTION = "file_execution"
    FILE_DROP = "file_drop"
    DATA = "data"
    COMPLETE = "complete"


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
        SignatureExpectationType(value.upper())
        return value


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


class SignatureOutputStructure(BaseModel):
    """Structured output to be serialized as a str in the callback payload yet data has to follow model."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    expectation_signatures: SignaturePayload

    def normalize_signature_payload(self) -> None:
        """
        Regroup signature_values by expectation_type within each target.
        """
        normalized_targets: list[TargetSignatures] = []

        for target in self.expectation_signatures.targets:
            if not target.signature_values:
                normalized_targets.append(target)
                continue

            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            order: list[str] = []

            for entry in target.signature_values:
                if entry.expectation_type not in order:
                    order.append(entry.expectation_type)
                grouped[entry.expectation_type].extend(entry.values)

            normalized_target = TargetSignatures(
                signature_target=target.signature_target,
                signature_values=[
                    ExpectationSignatureGroup(
                        expectation_type=expectation_type,
                        values=grouped[expectation_type],
                    )
                    for expectation_type in order
                ],
            )

            normalized_targets.append(normalized_target)

        self.expectation_signatures.targets = normalized_targets


class ExecutionDetails(BaseModel):
    """Helper to wrap the execution-related details for the callback payload."""

    model_config = ConfigDict(extra="forbid")

    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime | None = None

    execution_status: ExecutionStatus | None = None
    execution_action: InjectExecutionActions | None = None

    @computed_field
    @property
    def execution_message(self) -> str:
        action = self.execution_action.value if self.execution_action else "unknown"
        status = self.execution_action.value if self.execution_action else "unknown"
        return f"Current action: {action} - Current status: {status}"

    @computed_field
    @property
    def execution_duration(self) -> float:
        try:
            return (self.end_time - self.start_time).total_seconds()
        except:
            return 0.0

    def post_execution_update(self, tool_output: "ToolOutput", now: datetime) -> None:
        """
        Update execution-related metadata according to tool output and now timestamp.
        """
        self.end_time = now

        if tool_output.error_info and tool_output.error_info.exit_code != 0:
            self.execution_status = ExecutionStatus.ERROR
            if tool_output.error_info.crash_timestamp:
                self.end_time = datetime.strptime(
                    tool_output.error_info.crash_timestamp, "%Y-%m-%dT%H:%M:%SZ"
                )
        elif tool_output.timeout_info:
            self.execution_status = ExecutionStatus.TIMEOUT
        elif tool_output.status == "partial":
            self.execution_status = ExecutionStatus.ERROR
        else:
            self.execution_status = ExecutionStatus.EXECUTED

        self.execution_action = InjectExecutionActions("data")


class SignatureCallbackPayload(BaseModel):
    """Outer POST envelope validated by ``SignatureApiManager`` before wire transmission."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    execution_message: str
    execution_output_structured: str | None = None
    execution_status: str
    execution_duration: int | None = None
    execution_action: InjectExecutionActions | None = None

    @field_validator("execution_output_structured", mode="after")
    @classmethod
    def is_proper_signature_output_structure(cls, value: str) -> str | None:
        if value is None:
            return None
        TypeAdapter(SignatureOutputStructure).validate_json(value)
        return value

    @classmethod
    def build_from_models(
        cls, signatures: SignatureOutputStructure, execution_details: ExecutionDetails
    ):
        """Producing a SignatureCallbackPayload from the data of a SignatureOutputStructure and of a ExecutionDetails."""
        return cls(
            execution_message=execution_details.execution_message,
            execution_output_structured=signatures.model_dump_json(exclude_none=True),
            execution_status=execution_details.execution_status,
            execution_duration=(
                math.ceil(execution_details.execution_duration)
                if execution_details.execution_duration is not None
                else None
            ),
            execution_action=execution_details.execution_action,
        )


__all__ = [
    "PORT_IO_CONTRACT_VERSION",
    "SignatureExpectationType",
    "ExecutionStatus",
    "InjectExecutionActions",
    "SignatureValue",
    "ExpectationSignatureGroup",
    "SignatureTarget",
    "TargetSignatures",
    "SignaturePayload",
    "SignatureOutputStructure",
    "ExecutionDetails",
    "SignatureCallbackPayload",
]
