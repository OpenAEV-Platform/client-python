"""Tests for the sample platform payloads and the sources the payload models mirror.

Feature: Platform payload samples
  Each payload model is written by hand from the platform DTO it mirrors, and ships with
  one sample payload written from that DTO. A sample read with its model and written
  back is unchanged, the platform's dates are read whether it wrote them as ISO text or
  as epoch numbers, and every model names the DTO it mirrors.
"""

import json
from pathlib import Path
from typing import Any

import pytest
import xtm_oaev_sdk as sdk
from pydantic import TypeAdapter

FIXTURES = Path(__file__).parent / "fixtures"

#: Each payload model and the platform source it mirrors (openaev-platform repository).
PLATFORM_SOURCES = {
    "ExecutableInject": "openaev-api/src/main/java/io/openaev/execution/ExecutableInjectDTO.java",
    "ExecutableInjection": "openaev-model/src/main/java/io/openaev/database/model/Injection.java",
    "ExecutableInjectorContract": "openaev-model/src/main/java/io/openaev/database/model/InjectorContract.java",
    "EndpointTargetOutput": "openaev-api/src/main/java/io/openaev/rest/asset/endpoint/output/EndpointTargetOutput.java",
    "AgentOutput": "openaev-api/src/main/java/io/openaev/rest/asset/endpoint/form/AgentOutput.java",
    "AssetGroupSimple": "openaev-api/src/main/java/io/openaev/rest/asset_group/form/AssetGroupSimple.java",
    "InjectReceptionInput": "openaev-api/src/main/java/io/openaev/rest/inject/form/InjectReceptionInput.java",
    "InjectExecutionInput": "openaev-api/src/main/java/io/openaev/rest/inject/form/InjectExecutionInput.java",
    "InjectExpectationOutput": "openaev-api/src/main/java/io/openaev/api/expectations/dto/InjectExpectationOutput.java",
    "InjectExpectationSignature": "openaev-model/src/main/java/io/openaev/database/model/InjectExpectationSignature.java",
    "InjectExpectationResult": "openaev-model/src/main/java/io/openaev/database/model/InjectExpectationResult.java",
    "InjectExpectationUpdateFromCollectorInput": "openaev-api/src/main/java/io/openaev/rest/inject/form/InjectExpectationUpdateFromCollectorInput.java",
    "InjectExpectationBulkUpdateInput": "openaev-api/src/main/java/io/openaev/rest/inject/form/InjectExpectationBulkUpdateInput.java",
    "InjectExpectationTraceInput": "openaev-api/src/main/java/io/openaev/rest/inject_expectation_trace/form/InjectExpectationTraceInput.java",
    "InjectExpectationTraceBulkInsertInput": "openaev-api/src/main/java/io/openaev/rest/inject_expectation_trace/form/InjectExpectationTraceBulkInsertInput.java",
}


def _given_payload_model(name: str) -> Any:
    """Given the SDK models the "<name>" platform payload"""
    model = getattr(sdk, name, None)
    assert model is not None, f"Expected xtm_oaev_sdk.{name} to exist on public surface"
    return model


def _given_sample(fixture: str) -> Any:
    """Given the sample payload "<fixture>" written from its platform DTO"""
    return json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))


def _given_pending_expectation_dated(created_at: Any) -> dict[str, Any]:
    """Given a pending expectation the platform dated <created_at>"""
    expectation = dict(_given_sample("pending_expectations.json")[0])
    expectation["inject_expectation_created_at"] = created_at
    expectation["inject_expectation_updated_at"] = created_at
    return expectation


def _given_trace_dated(date: Any) -> dict[str, Any]:
    """Given an expectation trace dated <date>"""
    trace = dict(_given_sample("traces_bulk.json")["expectation_traces"][0])
    trace["inject_expectation_trace_date"] = date
    return trace


def _when_reading_and_writing_back(model: Any, payload: Any, many: bool) -> Any:
    """When the payload is read with that model and written back as JSON"""
    adapter = TypeAdapter(list[model] if many else model)
    value = adapter.validate_python(payload)
    return adapter.dump_python(value, mode="json", exclude_unset=True)


def _when_reading_the_docstring(model: Any) -> str:
    """When the model's documentation is read"""
    return model.__doc__ or ""


def _then_written_payload_is(written: Any, payload: Any) -> None:
    """Then the written payload is exactly the payload read"""
    assert written == payload


def _then_docstring_names(docstring: str, source: str) -> None:
    """Then the documentation names the platform source "<source>" """
    flat = " ".join(docstring.split())
    assert source in flat, f"Expected the docstring to name {source}, got: {flat}"


@pytest.mark.parametrize(
    "fixture, model_name, many",
    [
        ("inject_message.json", "ExecutableInject", False),
        ("execution_reception.json", "InjectReceptionInput", False),
        ("execution_callback.json", "InjectExecutionInput", False),
        ("pending_expectations.json", "InjectExpectationOutput", True),
        ("expectation_update.json", "InjectExpectationUpdateFromCollectorInput", False),
        ("expectation_bulk_update.json", "InjectExpectationBulkUpdateInput", False),
        ("traces_bulk.json", "InjectExpectationTraceBulkInsertInput", False),
    ],
)
def test_sample_payload_round_trips_unchanged(
    fixture: str, model_name: str, many: bool
) -> None:
    """It reads each sample payload with its model and writes it back unchanged.

    Scenario Outline: A sample payload round-trips unchanged
      Given the sample payload "<fixture>" written from its platform DTO
      And the SDK models the "<model>" platform payload
      When the payload is read with that model and written back as JSON
      Then the written payload is exactly the payload read
    """
    payload = _given_sample(fixture)
    model = _given_payload_model(model_name)
    written = _when_reading_and_writing_back(model, payload, many)
    _then_written_payload_is(written, payload)


@pytest.mark.parametrize("created_at", ["2026-11-05T20:00:00Z", 1762372800.0])
def test_pending_expectation_keeps_the_dates_as_the_platform_wrote_them(
    created_at: Any,
) -> None:
    """It reads a pending expectation dated as ISO text or as an epoch number.

    Scenario Outline: The platform's dates are read as written
      Given a pending expectation the platform dated <created_at>
      And the SDK models the "InjectExpectationOutput" platform payload
      When the payload is read with that model and written back as JSON
      Then the written payload is exactly the payload read
    """
    payload = _given_pending_expectation_dated(created_at)
    model = _given_payload_model("InjectExpectationOutput")
    written = _when_reading_and_writing_back(model, payload, False)
    _then_written_payload_is(written, payload)


@pytest.mark.parametrize("date", ["2026-11-05T20:01:00Z", 1762372860])
def test_expectation_trace_takes_an_iso_or_epoch_date(date: Any) -> None:
    """It accepts a trace dated as ISO text or as an epoch number.

    Scenario Outline: A trace date is written as given
      Given an expectation trace dated <date>
      And the SDK models the "InjectExpectationTraceInput" platform payload
      When the payload is read with that model and written back as JSON
      Then the written payload is exactly the payload read
    """
    payload = _given_trace_dated(date)
    model = _given_payload_model("InjectExpectationTraceInput")
    written = _when_reading_and_writing_back(model, payload, False)
    _then_written_payload_is(written, payload)


@pytest.mark.parametrize("model_name, source", sorted(PLATFORM_SOURCES.items()))
def test_payload_model_names_the_platform_dto_it_mirrors(
    model_name: str, source: str
) -> None:
    """It documents each payload model with the platform DTO it mirrors.

    Scenario Outline: A payload model names its platform DTO
      Given the SDK models the "<model>" platform payload
      When the model's documentation is read
      Then the documentation names the platform source "<source>"
    """
    model = _given_payload_model(model_name)
    docstring = _when_reading_the_docstring(model)
    _then_docstring_names(docstring, source)
