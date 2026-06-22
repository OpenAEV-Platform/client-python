from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev.signatures.models import ExecutionDetails, ExecutionSignature
from pyoaev.signatures.signature_manager import SignatureManager


@scenario(
    "features/signature_manager_post_execution.feature",
    "Successful execution updates end_time and execution_status in execution signatures and execution details",
)
def test_successful_execution_merges_post_execution_fields():
    pass


@scenario(
    "constraints/signature_manager_post_execution_constraints.feature",
    "Tool crash sets execution_status to failed and uses crash timestamp as end_time",
)
def test_tool_crash_sets_failed_status_and_crash_timestamp_end_time():
    pass


@scenario(
    "constraints/signature_manager_post_execution_constraints.feature",
    "Timeout sets execution_status to timeout and includes available partial results",
)
def test_timeout_sets_timeout_status_and_includes_partial_results():
    pass


@scenario(
    "constraints/signature_manager_post_execution_constraints.feature",
    "Timeout with no partial results still sets execution_status to timeout",
)
def test_timeout_without_partial_results_still_sets_timeout_status():
    pass


@pytest.fixture
def context():
    return {}


def _parse_iso8601_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@given(
    "a SignatureManager initialised with constructor SignatureManager(client, logger)"
)
def signature_manager(context):
    context["signature_manager"] = SignatureManager(MagicMock(), MagicMock())


@given(
    "a execution_signatures object containing:",
    target_fixture="execution_signatures",
)
def execution_signatures():
    return ExecutionSignature(
        source_ipv4="172.17.0.2",
        target_ipv4="10.0.0.1",
        target_hostname="host-a.internal",
        start_time="2024-06-26T06:00:00Z",
    )


@given(
    "a execution_details object containing:",
    target_fixture="execution_details",
)
def execution_details():
    return ExecutionDetails(
        execution_status="",
        start_time=datetime.strptime("2024-06-26T06:00:00Z", "%Y-%m-%dT%H:%M:%SZ"),
    )


@given(
    "a tool_output indicating successful completion with no errors and no timeout",
    target_fixture="tool_output",
)
def successful_tool_output():
    return {"status": "success"}


@given(
    'a tool_output containing error_info with exit_code=1 and crash_timestamp="2024-06-26T06:05:00Z"',
    target_fixture="tool_output",
)
def crashed_tool_output():
    return {
        "error_info": {
            "exit_code": 1,
            "crash_timestamp": "2024-06-26T06:05:00Z",
        }
    }


@given(
    'a tool_output containing timeout_info with partial_results=["result-A", "result-B"]',
    target_fixture="tool_output",
)
def timeout_tool_output_with_partial_results():
    return {"timeout_info": {"partial_results": ["result-A", "result-B"]}}


@given(
    "a tool_output containing timeout_info with no partial results available",
    target_fixture="tool_output",
)
def timeout_tool_output_with_no_partial_results():
    return {"timeout_info": {"partial_results": []}}


@when(
    "I call post_execution_updates with the execution_details, execution_signatures and tool_output"
)
def post_execution_update(
    context, execution_details, execution_signatures, tool_output
):
    context["signature_manager"].post_execution_updates(
        execution_details, execution_signatures, tool_output
    )
    context["execution_details_result"] = execution_details
    context["execution_signatures_result"] = execution_signatures


@then("the execution signature model contains every previous parameter unchanged")
def execution_signatures_unchanged(context, execution_signatures):
    basic_exec_sig = execution_signatures
    exec_sig_result = context["execution_signatures_result"]

    assert exec_sig_result.source_ipv4 == basic_exec_sig.source_ipv4
    assert exec_sig_result.source_ipv6 == basic_exec_sig.source_ipv6
    assert exec_sig_result.target_ipv4 == basic_exec_sig.target_ipv4
    assert exec_sig_result.target_ipv6 == basic_exec_sig.target_ipv6
    assert exec_sig_result.target_hostname == basic_exec_sig.target_hostname
    assert exec_sig_result.cloud_provider == basic_exec_sig.cloud_provider
    assert exec_sig_result.cloud_account_id == basic_exec_sig.cloud_account_id
    assert exec_sig_result.cloud_region == basic_exec_sig.cloud_region
    assert exec_sig_result.target_service == basic_exec_sig.target_service


@then(
    "the end_time parameter in the execution signature model is a UTC ISO 8601 string"
)
def result_contains_iso8601_end_time(context):
    end_time = context["execution_signatures_result"].end_time
    assert isinstance(end_time, str)
    _parse_iso8601_utc(end_time)


@then(
    parsers.parse(
        'this end_time is chronologically greater than or equal to start_time "{start_time}"'
    )
)
def end_time_at_or_after_start_time(context, start_time):
    end_time_dt = _parse_iso8601_utc(context["execution_signatures_result"].end_time)
    start_time_dt = _parse_iso8601_utc(start_time)
    assert end_time_dt >= start_time_dt


@then(parsers.parse('end_time equals "{expected_end_time}"'))
def end_time_equals(context, expected_end_time):
    assert context["execution_signatures_result"].end_time == expected_end_time


@then(
    'the returned dict contains the partial results ["result-A", "result-B"] from timeout_info'
)
def contains_timeout_partial_results(context):
    assert context["execution_signatures_result"].partial_results == [
        "result-A",
        "result-B",
    ]


@then("the execution details model contain every previous parameter pair unchanged")
def execution_details_unchanged(context, execution_details):
    basic_exec_details = execution_details
    exec_details_result = context["execution_details_result"]

    assert exec_details_result.start_time == basic_exec_details.start_time
    assert exec_details_result.execution_message == basic_exec_details.execution_message


@then("the end_time parameter in the execution details model is a datetime object")
def result_contains_datetime_end_time(context):
    end_time = context["execution_details_result"].end_time
    assert isinstance(end_time, datetime)


@then(
    parsers.parse(
        'the execution_status parameter in the execution details model is equal to "{status}"'
    )
)
@then(parsers.parse('execution_status equals "{status}"'))
def execution_status_equals(context, status):
    assert context["execution_details_result"].execution_status == status


@then(
    parsers.parse(
        'the execution_action parameter in the execution details model is equal to "{action}"'
    )
)
@then(parsers.parse('execution_action equals "{action}"'))
def execution_action_equals(context, action):
    assert context["execution_details_result"].execution_action == action
