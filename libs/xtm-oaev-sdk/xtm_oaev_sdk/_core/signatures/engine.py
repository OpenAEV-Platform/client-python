"""Signature engine: compile pre-execution signatures, merge tool output,
package the wire payload."""

from datetime import datetime, timezone
from typing import Any, Callable

from pydantic import ValidationError
from xtm_oaev_sdk.seam.common import OpenAEVError
from xtm_oaev_sdk.seam.port_io import (
    ExecutionDetails,
    ExpectationSignatureGroup,
    SignatureOutputStructure,
    SignaturePayload,
    SignatureTarget,
    SignatureValue,
    TargetSignatures,
)
from xtm_oaev_sdk.seam.signatures import (
    CloudInjectorConfig,
    ExecutionSignature,
    ExtraSignatureData,
    InjectorConfig,
    NetworkInjectorConfig,
    ToolOutput,
)

__all__ = ["SignatureEngine"]


class SignatureEngine:
    """Implements ``SignatureEnginePort``."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def validate_configs(self, configs: list[InjectorConfig]) -> None:
        if not configs:
            raise ValueError("build_execution_signatures requires at least one config")
        first_type = type(configs[0])
        for c in configs:
            if not isinstance(c, first_type):
                raise ValueError(
                    "build_execution_signatures does not mix injector config types; "
                    f"got {sorted({type(c).__name__ for c in configs})}"
                )

    def format_start_time(self, now: datetime) -> str:
        return now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def source_context(
        self,
        config: InjectorConfig,
        source_ipv4: Callable[[], str],
        source_ipv6: Callable[[], str | None],
    ) -> dict[str, Any]:
        if isinstance(config, NetworkInjectorConfig):
            return {"source_ipv4": source_ipv4(), "source_ipv6": source_ipv6()}
        if isinstance(config, CloudInjectorConfig):
            return {}
        raise TypeError(f"unsupported injector config type: {type(config).__name__}")

    def build_signature(
        self, config: InjectorConfig, start_time: str, source_context: dict[str, Any]
    ) -> ExecutionSignature:
        base: dict[str, Any] = {"start_time": start_time}
        base.update(source_context)
        base.update(config.model_dump(exclude_none=True))
        return ExecutionSignature(**base)

    def apply_tool_output(
        self,
        execution_details: ExecutionDetails,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        tool_output: dict[str, Any],
        now: Callable[[], datetime],
    ) -> None:
        try:
            tool_output = ToolOutput.model_validate(tool_output or {})
        except ValidationError as exc:
            raise OpenAEVError(error_message=f"Invalid tool_output: {exc}") from exc

        now = now()
        execution_details.post_execution_update(tool_output, now)
        if isinstance(execution_signatures, list):
            for exec_sig in execution_signatures:
                exec_sig.post_execution_update(tool_output, now)
        else:
            execution_signatures.post_execution_update(tool_output, now)

    def build_payload(
        self,
        execution_signatures: ExecutionSignature | list[ExecutionSignature],
        targets_meta: Any | list[Any],
        expectation_types: list[str],
        extra_signatures: ExtraSignatureData,
    ) -> dict[str, Any]:
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
                        expectation_type=expectation_type, values=values
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

    def output_structure(self, signatures: dict[str, Any]) -> SignatureOutputStructure:
        return SignatureOutputStructure(
            expectation_signatures=SignaturePayload(**signatures)
        )
