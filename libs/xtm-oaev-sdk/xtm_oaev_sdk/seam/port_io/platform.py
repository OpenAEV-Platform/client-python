"""The platform's own payloads, exchanged with injectors and collectors.

Each model mirrors one payload of the OpenAEV platform, key for key, so an injector or a
collector running without the platform reads and writes exactly the JSON the platform
would. Each model is written by hand from the platform DTO it mirrors, and its docstring
names that DTO's source file in the platform repository:

- ``ExecutableInject``: the inject message the platform publishes to an injector
  queue (``ExecutableInjectDTO``), with its ``injection``, ``assets`` and
  ``assetGroups``;
- ``InjectReceptionInput`` and ``InjectExecutionInput``: what an injector posts to
  ``/api/injects/execution/reception/{id}`` and ``/api/injects/execution/callback/{id}``;
- ``InjectExpectationOutput``: one pending expectation, as the platform serves it to a
  collector (``/api/injects/expectations/...``);
- ``InjectExpectationUpdateFromCollectorInput`` and ``InjectExpectationBulkUpdateInput``:
  a collector's answer (``PUT /api/injects/expectations/{id}`` and ``.../bulk``);
- ``InjectExpectationTraceInput`` and ``InjectExpectationTraceBulkInsertInput``: the
  traces a collector attaches (``POST /api/inject-expectations-traces/bulk``).

What the platform sends keeps the keys this module does not model (``extra="allow"``),
so nothing is lost when a payload is read and written back. What a connector sends
refuses any key the platform does not take (``extra="forbid"``). Dates stay as the
platform wrote them, ISO text or epoch numbers: they are not parsed.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator
from xtm_oaev_sdk.seam.port_io.models import ExecutionStatus, InjectExecutionActions

__all__ = [
    "AgentOutput",
    "AssetGroupSimple",
    "EndpointTargetOutput",
    "ExecutableInject",
    "ExecutableInjection",
    "ExecutableInjectorContract",
    "InjectExecutionInput",
    "InjectExpectationBulkUpdateInput",
    "InjectExpectationOutput",
    "InjectExpectationResult",
    "InjectExpectationSignature",
    "InjectExpectationTraceBulkInsertInput",
    "InjectExpectationTraceInput",
    "InjectExpectationUpdateFromCollectorInput",
    "InjectReceptionInput",
]

_FROM_PLATFORM = ConfigDict(extra="allow")
_TO_PLATFORM = ConfigDict(extra="forbid")


def _not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


# --- Inject message (platform -> injector) ---------------------------------------


class AgentOutput(BaseModel):
    """An agent of an asset target.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/asset/endpoint/form/AgentOutput.java``.
    """

    model_config = _FROM_PLATFORM

    agent_id: str
    agent_privilege: str | None = None
    agent_deployment_mode: str | None = None
    agent_executed_by_user: str | None = None
    agent_executor: JsonValue = None
    agent_active: bool | None = None
    agent_last_seen: JsonValue = None
    agent_version: str | None = None


class EndpointTargetOutput(BaseModel):
    """An asset target of an inject.

    Mirrors
    ``openaev-api/src/main/java/io/openaev/rest/asset/endpoint/output/EndpointTargetOutput.java``.
    """

    model_config = _FROM_PLATFORM

    asset_id: str
    asset_hostname: str | None = None
    asset_ips: list[str] = Field(default_factory=list)
    asset_seen_ip: str | None = None
    asset_agents: list[AgentOutput] = Field(default_factory=list)


class AssetGroupSimple(BaseModel):
    """An asset group target of an inject.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/asset_group/form/AssetGroupSimple.java``.
    """

    model_config = _FROM_PLATFORM

    asset_group_id: str
    asset_group_name: str | None = None


class ExecutableInjectorContract(BaseModel):
    """The injector contract of an inject (``inject_injector_contract``). The contract
    id is ``injector_contract_id``, and ``convertedContent`` (the parsed
    ``injector_contract_content``) holds it again as ``contract_id``.

    Mirrors ``openaev-model/src/main/java/io/openaev/database/model/InjectorContract.java``.
    """

    model_config = _FROM_PLATFORM

    injector_contract_id: str
    injector_contract_content: str | None = None
    convertedContent: dict[str, JsonValue] | None = None


class ExecutableInjection(BaseModel):
    """The inject itself (``injection``), as the platform serializes it.

    Mirrors ``openaev-model/src/main/java/io/openaev/database/model/Injection.java``.
    """

    model_config = _FROM_PLATFORM

    inject_id: str
    inject_title: str | None = None
    inject_content: dict[str, JsonValue] | None = None
    inject_injector_contract: ExecutableInjectorContract | None = None
    inject_documents: list[JsonValue] = Field(default_factory=list)


class ExecutableInject(BaseModel):
    """The inject message published to an injector queue.

    Mirrors ``openaev-api/src/main/java/io/openaev/execution/ExecutableInjectDTO.java``.
    """

    model_config = _FROM_PLATFORM

    injection: ExecutableInjection
    assets: list[EndpointTargetOutput] = Field(default_factory=list)
    assetGroups: list[AssetGroupSimple] = Field(default_factory=list)
    attachments: dict[str, JsonValue] | None = None


# --- Execution calls (injector -> platform) ----------------------------------------


class InjectReceptionInput(BaseModel):
    """Body of ``POST /api/injects/execution/reception/{inject_id}``.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/inject/form/InjectReceptionInput.java``.
    """

    model_config = _TO_PLATFORM

    tracking_total_count: int = 0


class InjectExecutionInput(BaseModel):
    """Body of ``POST /api/injects/execution/callback/{inject_id}``.

    ``execution_status`` is a platform status name, or ``SUCCESS`` in any case (the
    platform reads it as ``EXECUTED``). ``execution_output_structured`` is JSON text.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/inject/form/InjectExecutionInput.java``.
    """

    model_config = _TO_PLATFORM

    execution_message: str
    execution_output_structured: str | None = None
    execution_output_raw: str | None = None
    execution_status: str
    execution_duration: int = 0
    execution_action: InjectExecutionActions
    execution_context_identifiers: list[str] | None = Field(
        default=None, max_length=1000
    )

    @field_validator("execution_message", mode="after")
    @classmethod
    def is_not_blank(cls, value: str) -> str:
        return _not_blank(value)

    @field_validator("execution_status", mode="after")
    @classmethod
    def is_platform_status(cls, value: str) -> str:
        if value.upper() != "SUCCESS":
            ExecutionStatus(value)
        return value


# --- Pending expectations (platform -> collector) --------------------------------


class InjectExpectationSignature(BaseModel):
    """One signature of a pending expectation.

    Mirrors
    ``openaev-model/src/main/java/io/openaev/database/model/InjectExpectationSignature.java``.
    """

    model_config = _FROM_PLATFORM

    type: str
    value: str


class InjectExpectationResult(BaseModel):
    """One result of a pending expectation (``InjectExpectationResult``). Its own id
    is ``inject_expectation_id``, and its source keys are camelCase.

    Mirrors
    ``openaev-model/src/main/java/io/openaev/database/model/InjectExpectationResult.java``.
    """

    model_config = _FROM_PLATFORM

    inject_expectation_id: str | None = None
    sourceId: str | None = None
    sourceType: str | None = None
    sourceName: str | None = None
    sourceAssetId: str | None = None
    sourcePlatform: str | None = None
    date: JsonValue = None
    score: float | None = None
    result: str | None = None
    metadata: dict[str, str] | None = None
    inject_expectation_result_created_at: JsonValue = None
    inject_expectation_result_updated_at: JsonValue = None


class InjectExpectationOutput(BaseModel):
    """One pending expectation, as the platform serves it to a collector.
    ``inject_expiration_time`` is in seconds.

    Mirrors
    ``openaev-api/src/main/java/io/openaev/api/expectations/dto/InjectExpectationOutput.java``.
    """

    model_config = _FROM_PLATFORM

    inject_expectation_id: str
    inject_expectation_type: Literal[
        "ARTICLE",
        "CHALLENGE",
        "MANUAL",
        "PREVENTION",
        "DETECTION",
        "LOGGING",
        "VULNERABILITY",
    ]
    inject_expectation_name: str | None = None
    inject_expectation_description: str | None = None
    inject_expectation_score: float | None = None
    inject_expectation_expected_score: float | None = None
    inject_expiration_time: int | None = None
    inject_expectation_group: bool | None = None
    inject_expectation_order: int | None = None
    inject_expectation_status: (
        Literal["FAILED", "PENDING", "PARTIAL", "UNKNOWN", "SUCCESS"] | None
    ) = None
    inject_expectation_created_at: JsonValue = None
    inject_expectation_updated_at: JsonValue = None
    inject_expectation_signatures: list[InjectExpectationSignature] = Field(
        default_factory=list
    )
    inject_expectation_results: list[InjectExpectationResult] = Field(
        default_factory=list
    )
    inject_expectation_traces: list[JsonValue] = Field(default_factory=list)
    inject_expectation_exercise: str | None = None
    inject_expectation_inject: str | None = None
    inject_expectation_user: str | None = None
    inject_expectation_team: str | None = None
    inject_expectation_agent: str | None = None
    inject_expectation_asset: str | None = None
    inject_expectation_asset_group: str | None = None
    inject_expectation_article: str | None = None
    inject_expectation_challenge: str | None = None
    target_id: str | None = None
    inject_expectation_expected_security_platforms: list[str] | None = None
    inject_expectation_collector_missing_at_init: bool | None = None

    @field_validator("inject_expectation_signatures", mode="before")
    @classmethod
    def null_is_none(cls, value: JsonValue) -> JsonValue:
        # Earlier platforms serialize an expectation without signatures as null.
        return [] if value is None else value


# --- Collector answers (collector -> platform) -------------------------------------


class InjectExpectationUpdateFromCollectorInput(BaseModel):
    """Body of ``PUT /api/injects/expectations/{expectation_id}``. The platform
    ignores ``result``: it derives the label from ``is_success``.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/inject/form/InjectExpectationUpdateFromCollectorInput.java``.
    """

    model_config = _TO_PLATFORM

    collector_id: str
    result: str | None = None
    is_success: bool
    metadata: dict[str, str] | None = None


class InjectExpectationBulkUpdateInput(BaseModel):
    """Body of ``PUT /api/injects/expectations/bulk``: updates by expectation id.

    Mirrors
    ``openaev-api/src/main/java/io/openaev/rest/inject/form/InjectExpectationBulkUpdateInput.java``.
    """

    model_config = _TO_PLATFORM

    inputs: dict[str, InjectExpectationUpdateFromCollectorInput]


class InjectExpectationTraceInput(BaseModel):
    """One trace of ``POST /api/inject-expectations-traces/bulk``.
    ``inject_expectation_trace_source_id`` is the collector id, and
    ``inject_expectation_trace_match_type`` is ``marker``, ``source_ip`` or
    ``target_ip`` when given.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/inject_expectation_trace/form/InjectExpectationTraceInput.java``.
    """

    model_config = _TO_PLATFORM

    inject_expectation_trace_expectation: str
    inject_expectation_trace_source_id: str
    inject_expectation_trace_alert_name: str
    inject_expectation_trace_alert_link: str
    inject_expectation_trace_date: str | int | float
    inject_expectation_trace_match_type: str | None = None

    @field_validator(
        "inject_expectation_trace_expectation",
        "inject_expectation_trace_source_id",
        "inject_expectation_trace_alert_name",
        "inject_expectation_trace_alert_link",
        mode="after",
    )
    @classmethod
    def is_not_blank(cls, value: str) -> str:
        return _not_blank(value)


class InjectExpectationTraceBulkInsertInput(BaseModel):
    """Body of ``POST /api/inject-expectations-traces/bulk``.

    Mirrors ``openaev-api/src/main/java/io/openaev/rest/inject_expectation_trace/form/InjectExpectationTraceBulkInsertInput.java``.
    """

    model_config = _TO_PLATFORM

    expectation_traces: list[InjectExpectationTraceInput]
