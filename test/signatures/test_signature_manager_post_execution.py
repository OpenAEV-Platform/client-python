from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev.signatures.signature_manager import SignatureManager


@scenario(
    "features/signature_manager_post_execution.feature",
    "Successful execution merges end_time and execution_status into pre-execution fields",
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


@scenario(
    "features/signature_manager_post_execution.feature",
    "Multi-target pre-signatures merge into a list of post-signatures",
)
def test_multi_target_pre_signatures_merge_into_a_list_of_post_signatures():
    pass


@pytest.fixture
def context():
    return {}


def _parse_iso8601_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@given("a SignatureManager initialised with constructor SignatureManager(client, logger)")
def signature_manager(context):
    context["signature_manager"] = SignatureManager(MagicMock(), MagicMock())


@given(
    "a pre_signatures dict containing:",
    target_fixture="pre_signatures",
)
def pre_signatures():
    return {
        "source_ipv4": "172.17.0.2",
        "target_ipv4": "10.0.0.1",
        "target_hostname": "host-a.internal",
        "start_time": "2024-06-26T06:00:00Z",
    }


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


@when("I call compile_post_execution_signatures with the pre_signatures dict and tool_output")
def compile_post_execution_signatures(context, pre_signatures, tool_output):
    context["result"] = context["signature_manager"].compile_post_execution_signatures(
        pre_signatures, tool_output
    )


@then("the returned dict contains every key-value pair from pre_signatures unchanged")
@then(
    "all pre-execution fields from pre_signatures are present and unchanged in the returned dict"
)
def pre_signatures_unchanged(context, pre_signatures):
    result = context["result"]
    for key, value in pre_signatures.items():
        assert key in result
        assert result[key] == value


@then("the returned dict contains end_time as a UTC ISO 8601 string")
def result_contains_iso8601_end_time(context):
    end_time = context["result"]["end_time"]
    assert isinstance(end_time, str)
    _parse_iso8601_utc(end_time)


@then(
    parsers.parse(
        'end_time is chronologically greater than or equal to start_time "{start_time}"'
    )
)
def end_time_at_or_after_start_time(context, start_time):
    end_time_dt = _parse_iso8601_utc(context["result"]["end_time"])
    start_time_dt = _parse_iso8601_utc(start_time)
    assert end_time_dt >= start_time_dt


@then(parsers.parse('the returned dict contains execution_status equal to "{status}"'))
@then(parsers.parse('execution_status equals "{status}"'))
def execution_status_equals(context, status):
    assert context["result"]["execution_status"] == status


@then(parsers.parse('end_time equals "{expected_end_time}"'))
def end_time_equals(context, expected_end_time):
    assert context["result"]["end_time"] == expected_end_time


@then(
    'the returned dict contains the partial results ["result-A", "result-B"] from timeout_info'
)
def contains_timeout_partial_results(context):
    assert context["result"]["partial_results"] == ["result-A", "result-B"]


# --------------------------------------------------
# Multi-target post-execution scenario
# --------------------------------------------------


@given(
    "the pre_signatures is replaced by a list of 3 dicts each with a distinct target_ipv4",
    target_fixture="pre_signatures",
)
def pre_signatures_multi_target_list():
    return [
        {
            "source_ipv4": "172.17.0.2",
            "target_ipv4": "10.0.0.1",
            "start_time": "2024-06-26T06:00:00Z",
        },
        {
            "source_ipv4": "172.17.0.2",
            "target_ipv4": "10.0.0.2",
            "start_time": "2024-06-26T06:00:00Z",
        },
        {
            "source_ipv4": "172.17.0.2",
            "target_ipv4": "10.0.0.3",
            "start_time": "2024-06-26T06:00:00Z",
        },
    ]


@then("the returned value is a list of exactly 3 dicts")
def result_is_list_of_three_dicts(context):
    result = context["result"]
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(item, dict) for item in result)


@then(
    parsers.parse(
        'every dict in the returned list contains execution_status equal to "{status}"'
    )
)
def every_dict_has_execution_status(context, status):
    for item in context["result"]:
        assert item["execution_status"] == status


@then("every dict in the returned list contains end_time as a UTC ISO 8601 string")
def every_dict_has_iso8601_end_time(context):
    for item in context["result"]:
        assert isinstance(item["end_time"], str)
        _parse_iso8601_utc(item["end_time"])


@then(
    "every dict in the returned list preserves its original target_ipv4 and source_ipv4 fields"
)
def every_dict_preserves_pre_execution_fields(context, pre_signatures):
    result = context["result"]
    assert len(result) == len(pre_signatures)
    for original, merged in zip(pre_signatures, result):
        assert merged["target_ipv4"] == original["target_ipv4"]
        assert merged["source_ipv4"] == original["source_ipv4"]
