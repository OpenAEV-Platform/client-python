"""Tests for the platform payloads exchanged with injectors and collectors.

Feature: Platform payloads
  Injectors and collectors exchange JSON payloads with the OpenAEV platform: the inject
  message an injector consumes, the execution calls it sends back, the pending
  expectations a collector reads, and the updates and traces it answers with.
  The SDK models each payload exactly as the platform publishes or accepts it, so a
  connector running without the platform reads and writes the same JSON.
"""

from typing import Any, NamedTuple

import pytest
import xtm_oaev_sdk as sdk
from pydantic import ValidationError


class Reading(NamedTuple):
    value: Any
    error: ValidationError | None


def _given_payload_model(name: str) -> Any:
    """Given the SDK models the "<name>" platform payload"""
    model = getattr(sdk, name, None)
    assert model is not None, f"Expected xtm_oaev_sdk.{name} to exist on public surface"
    return model


def _given_platform_inject_message() -> dict[str, Any]:
    """Given an inject message as the platform publishes it to an injector queue"""
    return {
        "injection": {
            "inject_id": "8a4f1f0e-2c4b-4f43-9d5e-0b6f5b6f1a01",
            "inject_title": "Scan the DMZ",
            "inject_content": {
                "target_selector": "assets",
                "expectations": [
                    {
                        "expectation_type": "DETECTION",
                        "expectation_name": "Detection",
                        "expectation_score": 100.0,
                        "expectation_expectation_group": False,
                        "expectation_expiration_time": 21600,
                    }
                ],
            },
            "inject_injector_contract": {
                "injector_contract_id": "5c8b6c3e-tcp-connect",
                "injector_contract_content": '{"contract_id": "5c8b6c3e-tcp-connect"}',
                "convertedContent": {"contract_id": "5c8b6c3e-tcp-connect"},
                "injector_contract_labels": {"en": "TCP connect scan"},
            },
            "inject_documents": [],
            "inject_status": None,
        },
        "assets": [
            {
                "asset_id": "0d3f7d1a-web-01",
                "asset_hostname": "web-01",
                "asset_ips": ["10.0.0.5"],
                "asset_seen_ip": "10.0.0.5",
                "asset_agents": [{"agent_id": "c1b2-agent", "agent_active": True}],
            }
        ],
        "assetGroups": [{"asset_group_id": "f00d-dmz", "asset_group_name": "DMZ"}],
        "attachments": None,
    }


def _given_execution_callback(**overrides: Any) -> dict[str, Any]:
    """Given an execution callback as an injector sends it"""
    payload: dict[str, Any] = {
        "execution_message": "Scan completed",
        "execution_output_structured": '{"scan_results": [{"host": "10.0.0.5"}]}',
        "execution_output_raw": "PORT   STATE SERVICE\n22/tcp open  ssh",
        "execution_status": "SUCCESS",
        "execution_duration": 3,
        "execution_action": "complete",
        "execution_context_identifiers": ["0d3f7d1a-web-01"],
    }
    payload.update(overrides)
    return payload


def _given_pending_expectation(**overrides: Any) -> dict[str, Any]:
    """Given a pending expectation as the platform serves it to a collector"""
    payload: dict[str, Any] = {
        "inject_expectation_id": "4e5d-expectation",
        "inject_expectation_type": "DETECTION",
        "inject_expectation_name": "Detection",
        "inject_expectation_description": None,
        "inject_expectation_score": None,
        "inject_expectation_expected_score": 100.0,
        "inject_expiration_time": 21600,
        "inject_expectation_group": False,
        "inject_expectation_order": None,
        "inject_expectation_status": "PENDING",
        "inject_expectation_created_at": "2026-11-05T20:00:00Z",
        "inject_expectation_updated_at": "2026-11-05T20:00:00Z",
        "inject_expectation_signatures": [
            {"type": "parent_process_name", "value": "oaev-implant-8a4f"}
        ],
        "inject_expectation_results": [
            {
                "inject_expectation_id": "9b9b-result",
                "sourceId": "c0ffee-collector",
                "sourceType": "collector",
                "sourceName": "Splunk ES",
                "sourceAssetId": None,
                "sourcePlatform": "SIEM",
                "date": "2026-11-05T20:01:00Z",
                "score": 0.0,
                "result": "Not Detected",
                "metadata": {},
                "inject_expectation_result_created_at": "2026-11-05T20:01:00Z",
                "inject_expectation_result_updated_at": "2026-11-05T20:01:00Z",
            }
        ],
        "inject_expectation_traces": [],
        "inject_expectation_exercise": None,
        "inject_expectation_inject": "8a4f1f0e-2c4b-4f43-9d5e-0b6f5b6f1a01",
        "inject_expectation_user": None,
        "inject_expectation_team": None,
        "inject_expectation_agent": "c1b2-agent",
        "inject_expectation_asset": "0d3f7d1a-web-01",
        "inject_expectation_asset_group": None,
        "inject_expectation_article": None,
        "inject_expectation_challenge": None,
        "target_id": "c1b2-agent",
        "inject_expectation_expected_security_platforms": ["SIEM"],
        "inject_expectation_collector_missing_at_init": False,
    }
    payload.update(overrides)
    return payload


def _given_collector_update(**overrides: Any) -> dict[str, Any]:
    """Given an expectation update as a collector sends it"""
    payload: dict[str, Any] = {
        "collector_id": "c0ffee-collector",
        "result": "Detected",
        "is_success": True,
        "metadata": {"alertId": "a-42"},
    }
    payload.update(overrides)
    return payload


def _given_expectation_trace(**overrides: Any) -> dict[str, Any]:
    """Given an expectation trace as a collector sends it"""
    payload: dict[str, Any] = {
        "inject_expectation_trace_expectation": "4e5d-expectation",
        "inject_expectation_trace_source_id": "c0ffee-collector",
        "inject_expectation_trace_alert_name": "Suspicious port scan",
        "inject_expectation_trace_alert_link": "https://siem.example/alerts/a-42",
        "inject_expectation_trace_date": "2026-11-05T20:01:00Z",
        "inject_expectation_trace_match_type": "marker",
    }
    payload.update(overrides)
    return payload


def _given_without(payload: dict[str, Any], field: str) -> dict[str, Any]:
    """Given that payload without its "<field>" field"""
    return {key: value for key, value in payload.items() if key != field}


def _when_reading(model: Any, payload: Any) -> Reading:
    """When the payload is read with that model"""
    try:
        return Reading(model.model_validate(payload), None)
    except ValidationError as error:
        return Reading(None, error)


def _when_writing(reading: Reading) -> dict[str, Any]:
    """When the payload read is written back as JSON"""
    return reading.value.model_dump(mode="json", exclude_unset=True)


def _when_writing_with_defaults(reading: Reading) -> dict[str, Any]:
    """When the payload read is written back as JSON"""
    return reading.value.model_dump(mode="json")


def _then_payload_is_read(reading: Reading) -> None:
    """Then the payload is read"""
    assert reading.error is None, f"Expected the payload to be read: {reading.error}"


def _then_payload_is_refused(reading: Reading, field: str) -> None:
    """Then the payload is refused because of its "<field>" field"""
    assert reading.error is not None, "Expected the payload to be refused"
    failing = {str(part) for error in reading.error.errors() for part in error["loc"]}
    assert field in failing, f"Expected {field} to fail, got {failing}"


def _then_written_payload_is(written: dict[str, Any], payload: dict[str, Any]) -> None:
    """Then the written payload is exactly the payload read"""
    assert written == payload


def _then_written_field_is(written: dict[str, Any], field: str, value: Any) -> None:
    """Then the written "<field>" is <value>"""
    assert written[field] == value


def _then_expectation_has_no_signature(reading: Reading) -> None:
    """Then the expectation has no signature"""
    assert reading.value.inject_expectation_signatures == []


def _then_contract_version_is(version: str, expected: str) -> None:
    """Then the contract version is "<expected>" """
    assert version == expected


def test_inject_message_is_kept_as_the_platform_publishes_it() -> None:
    """It reads an inject message and writes it back unchanged, unmodelled keys included.

    Scenario: An inject message is kept as the platform publishes it
      Given the SDK models the "ExecutableInject" platform payload
      And an inject message as the platform publishes it to an injector queue
      When the payload is read with that model
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("ExecutableInject")
    payload = _given_platform_inject_message()
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


def test_inject_message_without_its_injection_is_refused() -> None:
    """It refuses an inject message that carries no injection.

    Scenario: An inject message without its injection is refused
      Given the SDK models the "ExecutableInject" platform payload
      And an inject message as the platform publishes it to an injector queue
      And that payload without its "injection" field
      When the payload is read with that model
      Then the payload is refused because of its "injection" field
    """
    model = _given_payload_model("ExecutableInject")
    payload = _given_without(_given_platform_inject_message(), "injection")
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, "injection")


def test_execution_reception_counts_no_tracking_by_default() -> None:
    """It sends a tracking count of 0 when an injector gives none, as the platform reads it.

    Scenario: An execution reception counts no tracking by default
      Given the SDK models the "InjectReceptionInput" platform payload
      When the payload is read with that model
      And the payload read is written back as JSON
      Then the written "tracking_total_count" is 0
    """
    model = _given_payload_model("InjectReceptionInput")
    reading = _when_reading(model, {})
    written = _when_writing_with_defaults(reading)
    _then_written_field_is(written, "tracking_total_count", 0)


def test_execution_callback_is_kept_as_the_platform_takes_it() -> None:
    """It keeps every field of an execution callback, structured output as text.

    Scenario: An execution callback is kept as the platform takes it
      Given the SDK models the "InjectExecutionInput" platform payload
      And an execution callback as an injector sends it
      When the payload is read with that model
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("InjectExecutionInput")
    payload = _given_execution_callback()
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


@pytest.mark.parametrize(
    "status", ["SUCCESS", "success", "EXECUTED", "ERROR", "ASSET_CLEARANCE_RESTRICTED"]
)
def test_execution_callback_accepts_the_statuses_the_platform_takes(
    status: str,
) -> None:
    """It accepts every status name the platform knows, and SUCCESS in any case.

    Scenario Outline: An execution callback accepts the statuses the platform takes
      Given the SDK models the "InjectExecutionInput" platform payload
      And an execution callback as an injector sends it, with status "<status>"
      When the payload is read with that model
      Then the payload is read

      Examples:
        | status                     |
        | SUCCESS                    |
        | success                    |
        | EXECUTED                   |
        | ERROR                      |
        | ASSET_CLEARANCE_RESTRICTED |
    """
    model = _given_payload_model("InjectExecutionInput")
    payload = _given_execution_callback(execution_status=status)
    reading = _when_reading(model, payload)
    _then_payload_is_read(reading)


@pytest.mark.parametrize("status", ["DONE", "executed"])
def test_execution_callback_refuses_a_status_the_platform_does_not_know(
    status: str,
) -> None:
    """It refuses a status the platform would reject.

    Scenario Outline: An execution callback refuses a status the platform does not know
      Given the SDK models the "InjectExecutionInput" platform payload
      And an execution callback as an injector sends it, with status "<status>"
      When the payload is read with that model
      Then the payload is refused because of its "execution_status" field

      Examples:
        | status   |
        | DONE     |
        | executed |
    """
    model = _given_payload_model("InjectExecutionInput")
    payload = _given_execution_callback(execution_status=status)
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, "execution_status")


@pytest.mark.parametrize("field", ["execution_action", "execution_message"])
def test_execution_callback_requires_what_the_platform_needs(field: str) -> None:
    """It refuses an execution callback without an action or a message.

    Scenario Outline: An execution callback requires what the platform needs
      Given the SDK models the "InjectExecutionInput" platform payload
      And an execution callback as an injector sends it
      And that payload without its "<field>" field
      When the payload is read with that model
      Then the payload is refused because of its "<field>" field

      Examples:
        | field             |
        | execution_action  |
        | execution_message |
    """
    model = _given_payload_model("InjectExecutionInput")
    payload = _given_without(_given_execution_callback(), field)
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, field)


def test_pending_expectation_is_kept_as_the_platform_serves_it() -> None:
    """It reads a pending expectation and writes it back unchanged, results included.

    Scenario: A pending expectation is kept as the platform serves it
      Given the SDK models the "InjectExpectationOutput" platform payload
      And a pending expectation as the platform serves it to a collector
      When the payload is read with that model
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("InjectExpectationOutput")
    payload = _given_pending_expectation()
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


def test_pending_expectation_of_an_unknown_type_is_refused() -> None:
    """It refuses an expectation type the platform does not have.

    Scenario: A pending expectation of an unknown type is refused
      Given the SDK models the "InjectExpectationOutput" platform payload
      And a pending expectation as the platform serves it, with type "TELEMETRY"
      When the payload is read with that model
      Then the payload is refused because of its "inject_expectation_type" field
    """
    model = _given_payload_model("InjectExpectationOutput")
    payload = _given_pending_expectation(inject_expectation_type="TELEMETRY")
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, "inject_expectation_type")


def test_collector_update_is_kept_as_the_platform_takes_it() -> None:
    """It keeps every field of an expectation update.

    Scenario: A collector update is kept as the platform takes it
      Given the SDK models the "InjectExpectationUpdateFromCollectorInput" platform payload
      And an expectation update as a collector sends it
      When the payload is read with that model
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("InjectExpectationUpdateFromCollectorInput")
    payload = _given_collector_update()
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


@pytest.mark.parametrize("field", ["collector_id", "is_success"])
def test_collector_update_requires_what_the_platform_needs(field: str) -> None:
    """It refuses an expectation update without its collector or its outcome.

    Scenario Outline: A collector update requires what the platform needs
      Given the SDK models the "InjectExpectationUpdateFromCollectorInput" platform payload
      And an expectation update as a collector sends it
      And that payload without its "<field>" field
      When the payload is read with that model
      Then the payload is refused because of its "<field>" field

      Examples:
        | field        |
        | collector_id |
        | is_success   |
    """
    model = _given_payload_model("InjectExpectationUpdateFromCollectorInput")
    payload = _given_without(_given_collector_update(), field)
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, field)


def test_bulk_update_maps_expectation_ids_to_their_update() -> None:
    """It keeps a bulk update as expectation ids mapped to their update.

    Scenario: A bulk update maps expectation ids to their update
      Given the SDK models the "InjectExpectationBulkUpdateInput" platform payload
      And an expectation update as a collector sends it
      When the payload is read with that model, under "inputs" for "4e5d-expectation"
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("InjectExpectationBulkUpdateInput")
    payload = {"inputs": {"4e5d-expectation": _given_collector_update()}}
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


def test_expectation_trace_is_kept_as_the_platform_takes_it() -> None:
    """It keeps every field of an expectation trace.

    Scenario: An expectation trace is kept as the platform takes it
      Given the SDK models the "InjectExpectationTraceInput" platform payload
      And an expectation trace as a collector sends it
      When the payload is read with that model
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("InjectExpectationTraceInput")
    payload = _given_expectation_trace()
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


@pytest.mark.parametrize(
    "field",
    [
        "inject_expectation_trace_expectation",
        "inject_expectation_trace_source_id",
        "inject_expectation_trace_alert_name",
        "inject_expectation_trace_alert_link",
        "inject_expectation_trace_date",
    ],
)
def test_expectation_trace_requires_what_the_platform_needs(field: str) -> None:
    """It refuses an expectation trace missing one of its mandatory fields.

    Scenario Outline: An expectation trace requires what the platform needs
      Given the SDK models the "InjectExpectationTraceInput" platform payload
      And an expectation trace as a collector sends it
      And that payload without its "<field>" field
      When the payload is read with that model
      Then the payload is refused because of its "<field>" field

      Examples:
        | field                                |
        | inject_expectation_trace_expectation |
        | inject_expectation_trace_source_id   |
        | inject_expectation_trace_alert_name  |
        | inject_expectation_trace_alert_link  |
        | inject_expectation_trace_date        |
    """
    model = _given_payload_model("InjectExpectationTraceInput")
    payload = _given_without(_given_expectation_trace(), field)
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, field)


def test_trace_bulk_insert_lists_the_traces() -> None:
    """It keeps a bulk trace insert as the list of its traces.

    Scenario: A trace bulk insert lists the traces
      Given the SDK models the "InjectExpectationTraceBulkInsertInput" platform payload
      And an expectation trace as a collector sends it
      When the payload is read with that model, under "expectation_traces"
      And the payload read is written back as JSON
      Then the payload is read
      And the written payload is exactly the payload read
    """
    model = _given_payload_model("InjectExpectationTraceBulkInsertInput")
    payload = {"expectation_traces": [_given_expectation_trace()]}
    reading = _when_reading(model, payload)
    written = _when_writing(reading)
    _then_payload_is_read(reading)
    _then_written_payload_is(written, payload)


# ---- Constraints identified ----


def test_execution_callback_refuses_a_field_the_platform_does_not_take() -> None:
    """It refuses a field the platform does not take, so nothing invented is sent.

    Scenario: An execution callback refuses a field the platform does not take
      Given the SDK models the "InjectExecutionInput" platform payload
      And an execution callback as an injector sends it, with "execution_kind" set
      When the payload is read with that model
      Then the payload is refused because of its "execution_kind" field
    """
    model = _given_payload_model("InjectExecutionInput")
    payload = _given_execution_callback(execution_kind="complete")
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, "execution_kind")


def test_execution_callback_refuses_more_than_1000_context_identifiers() -> None:
    """It refuses more than 1000 context identifiers, as the platform does.

    Scenario: An execution callback refuses more than 1000 context identifiers
      Given the SDK models the "InjectExecutionInput" platform payload
      And an execution callback as an injector sends it, with 1001 context identifiers
      When the payload is read with that model
      Then the payload is refused because of its "execution_context_identifiers" field
    """
    model = _given_payload_model("InjectExecutionInput")
    identifiers = [f"target-{index}" for index in range(1001)]
    payload = _given_execution_callback(execution_context_identifiers=identifiers)
    reading = _when_reading(model, payload)
    _then_payload_is_refused(reading, "execution_context_identifiers")


def test_pending_expectation_reads_null_signatures_as_none() -> None:
    """It reads null signatures as an empty list, as earlier platforms send them.

    Scenario: A pending expectation reads null signatures as none
      Given the SDK models the "InjectExpectationOutput" platform payload
      And a pending expectation as the platform serves it, with null signatures
      When the payload is read with that model
      Then the payload is read
      And the expectation has no signature
    """
    model = _given_payload_model("InjectExpectationOutput")
    payload = _given_pending_expectation(inject_expectation_signatures=None)
    reading = _when_reading(model, payload)
    _then_payload_is_read(reading)
    _then_expectation_has_no_signature(reading)


def test_payload_contract_version_announces_the_platform_payloads() -> None:
    """It announces the platform payloads with a minor contract version.

    Scenario: The payload contract version announces the platform payloads
      Given the SDK models the "PORT_IO_CONTRACT_VERSION" platform payload
      Then the contract version is "1.1.0"
    """
    version = _given_payload_model("PORT_IO_CONTRACT_VERSION")
    _then_contract_version_is(version, "1.1.0")
