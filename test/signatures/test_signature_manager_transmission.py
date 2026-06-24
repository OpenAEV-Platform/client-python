import ipaddress
import json
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from pytest_bdd import given, parsers, scenario, then, when

from pyoaev.apis.signature import SignatureApiManager
from pyoaev.exceptions import OpenAEVUpdateError, SignatureTransmissionError
from pyoaev.signatures.models import ExecutionDetails
from pyoaev.signatures.signature_manager import SignatureManager


@scenario(
    "features/signature_manager_transmission.feature",
    "HTTP 2xx response is treated as successful transmission",
)
def test_http_2xx_response_is_treated_as_successful_transmission():
    pass


@scenario(
    "features/signature_manager_transmission.feature",
    "send_signatures posts to the inject callback with the agreed nested schema",
)
def test_send_signatures_posts_with_agreed_nested_schema():
    pass


@scenario(
    "constraints/signature_manager_transmission_constraints.feature",
    "Payload exceeding MAX_PAYLOAD_SIZE is split into multiple sequential envelopes",
)
def test_payload_exceeding_max_payload_size_is_split_into_sequential_envelopes():
    pass


@scenario(
    "constraints/signature_manager_transmission_constraints.feature",
    "HTTP 5xx response triggers exponential backoff retry for up to 3 additional attempts",
)
def test_http_5xx_response_triggers_exponential_backoff_retry():
    pass


@scenario(
    "constraints/signature_manager_transmission_constraints.feature",
    "HTTP 4xx response raises an exception immediately with no retries and no sleep",
)
def test_http_4xx_response_raises_exception_immediately():
    pass


@scenario(
    "features/signature_manager_transmission.feature",
    "resolve_container_ip returns a valid IPv4 in each supported execution environment",
)
def test_resolve_container_ip_returns_valid_ipv4():
    pass


@scenario(
    "constraints/signature_manager_transmission_constraints.feature",
    "resolve_container_ip returns unknown and emits exactly one warning when all strategies fail",
)
def test_resolve_container_ip_returns_unknown_when_all_strategies_fail():
    pass


@scenario(
    "features/signature_manager_transmission.feature",
    "Payload schema groups signature values by expectation_type within each target",
)
def test_payload_schema_groups_signature_values_by_expectation_type():
    pass


@pytest.fixture
def context():
    return {}


_CANONICAL_SIGNATURE_TARGET = {
    "agent": "b044fbc7-f277-4c8c-aeae-5c5497598c51",
    "asset": "asset-host-a",
    "asset_group": "asset-group-internal",
}


def _extract_targets(body: dict) -> list[dict]:
    """Parse targets from the SignatureCallbackPayload wire format."""
    sig_data = json.loads(body["execution_output_structured"])
    return sig_data["signatures"]["targets"]


def _build_signature_payload(
    signature_value="203.0.113.5",
    expectation_types=None,
):
    if expectation_types is None:
        expectation_types = ["DETECTION"]
    return {
        "targets": [
            {
                "signature_target": dict(_CANONICAL_SIGNATURE_TARGET),
                "signature_values": [
                    {
                        "expectation_type": expectation_type,
                        "values": [
                            {
                                "signature_type": "public_ip",
                                "signature_value": (
                                    signature_value
                                    if expectation_type == "DETECTION"
                                    else "198.51.100.10"
                                ),
                            }
                        ],
                    }
                    for expectation_type in expectation_types
                ],
            }
        ]
    }


@given(
    "a SignatureManager initialised with constructor SignatureManager(client, logger)"
)
def signature_manager(context, monkeypatch):
    logger = MagicMock()
    mock_client = MagicMock()
    sleep_mock = MagicMock()
    captured_calls = []

    def _http_post(*args, **kwargs):
        path = kwargs.get("path", args[0] if args else None)
        post_data = kwargs.get("post_data", args[1] if len(args) > 1 else None)
        captured_calls.append(
            {
                "path": path,
                "post_data": post_data,
            }
        )
        status_plan = context.get("status_plan", [200])
        status_code = status_plan[min(len(captured_calls) - 1, len(status_plan) - 1)]
        if status_code >= 400:
            raise OpenAEVUpdateError(
                f"HTTP {status_code}",
                response_code=status_code,
                response_body=context.get("error_body", "").encode(),
            )
        return SimpleNamespace(status_code=status_code)

    mock_client.http_post.side_effect = _http_post

    # Wire up the real SignatureApi so delegation works
    sig_api = SignatureApiManager(mock_client)
    mock_client.signature = sig_api

    monkeypatch.setattr(
        "pyoaev.apis.signature.time.sleep",
        sleep_mock,
    )

    context["logger"] = logger
    context["mock_client"] = mock_client
    context["sleep_mock"] = sleep_mock
    context["captured_calls"] = captured_calls
    context["status_plan"] = [200]
    context["error_body"] = ""
    context["inject_id"] = "inject-abc-001"
    context["signatures"] = _build_signature_payload()
    context["signature_manager"] = SignatureManager(mock_client, logger=logger)


@given(parsers.parse('a compiled post-execution payload for inject_id "{inject_id}"'))
def compiled_post_execution_payload(context, inject_id):
    context["inject_id"] = inject_id
    context["signatures"] = _build_signature_payload()


@given(parsers.parse("an updated post-execution execution details object"))
def updated_post_execution_execution_details(context):
    execution_details = ExecutionDetails(
        execution_status="success",
        execution_action="complete",
    )
    execution_details.end_time = execution_details.start_time + timedelta(0.1)
    context["execution_details"] = execution_details


@given(
    parsers.parse(
        'a compiled payload with 1 target, expectation_type "{expectation_type}", signature_type "{signature_type}", signature_value "{signature_value}"'
    )
)
def compiled_payload_single_target(
    context,
    expectation_type,
    signature_type,
    signature_value,
):
    context["signatures"] = {
        "targets": [
            {
                "signature_target": dict(_CANONICAL_SIGNATURE_TARGET),
                "signature_values": [
                    {
                        "expectation_type": expectation_type,
                        "values": [
                            {
                                "signature_type": signature_type,
                                "signature_value": signature_value,
                            }
                        ],
                    }
                ],
            }
        ]
    }


@given(
    "a compiled payload whose serialised size exceeds MAX_PAYLOAD_SIZE by at least a factor of 2"
)
def compiled_large_payload(context):
    context["signature_manager"] = SignatureManager(
        context["mock_client"],
        logger=context["logger"],
        max_payload_size=700,
    )
    context["signatures"] = {
        "targets": [
            {
                "signature_target": {
                    "agent": f"agent-{index:08d}-0000-0000-0000-000000000000",
                    "asset": f"asset-{index}",
                    "asset_group": "asset-group-bulk",
                },
                "signature_values": [
                    {
                        "expectation_type": "DETECTION",
                        "values": [
                            {
                                "signature_type": "public_ip",
                                "signature_value": "203.0.113.123",
                            },
                            {
                                "signature_type": "hostname",
                                "signature_value": f"host-{index}." + ("a" * 94),
                            },
                        ],
                    }
                ],
            }
            for index in range(6)
        ]
    }


@given(parsers.parse("the backend responds with HTTP {status_code:d}"))
def backend_responds_with_http_status(context, status_code):
    context["status_plan"] = [status_code]
    context["error_body"] = ""


@given("the backend responds with HTTP 503 on every attempt")
def backend_responds_with_http_503_every_time(context):
    context["status_plan"] = [503, 503, 503, 503]


@given(
    parsers.parse("the backend responds with HTTP {status_code:d} and body '{body}'")
)
def backend_responds_with_http_status_and_body(context, status_code, body):
    context["status_plan"] = [status_code]
    context["error_body"] = body


@given(parsers.parse('a SignatureManager running in a "{environment}" environment'))
def signature_manager_environment(context, monkeypatch, environment):
    if environment == "Docker":
        monkeypatch.setattr(
            "pyoaev.signatures.signature_manager.socket.gethostbyname",
            lambda _: "172.17.0.2",
        )
        monkeypatch.setattr(
            "pyoaev.signatures.signature_manager.subprocess.run",
            lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="172.17.0.2\n",
            ),
        )
    elif environment == "Kubernetes":
        monkeypatch.setattr(
            "pyoaev.signatures.signature_manager.socket.gethostbyname",
            lambda _: (_ for _ in ()).throw(OSError("socket fail")),
        )
        monkeypatch.setattr(
            "pyoaev.signatures.signature_manager.subprocess.run",
            lambda *args, **kwargs: SimpleNamespace(
                returncode=0,
                stdout="10.244.0.8\n",
            ),
        )
    else:
        monkeypatch.setattr(
            "pyoaev.signatures.signature_manager.socket.gethostbyname",
            lambda _: "192.0.2.20",
        )


@given("all IP resolution strategies are mocked to fail")
def all_ip_resolution_strategies_fail(context, monkeypatch):
    monkeypatch.setattr(
        "pyoaev.signatures.signature_manager.socket.gethostbyname",
        lambda _: (_ for _ in ()).throw(OSError("socket fail")),
    )
    monkeypatch.setattr(
        "pyoaev.signatures.signature_manager.subprocess.run",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("command fail")),
    )


@given(
    parsers.parse(
        'a compiled payload for 1 target with signatures of expectation_type "{expectation_a}" and expectation_type "{expectation_b}"'
    )
)
def compiled_payload_grouped_by_expectation(
    context,
    expectation_a,
    expectation_b,
):
    context["signatures"] = {
        "targets": [
            {
                "signature_target": dict(_CANONICAL_SIGNATURE_TARGET),
                "signature_values": [
                    {
                        "expectation_type": expectation_a,
                        "values": [
                            {
                                "signature_type": "public_ip",
                                "signature_value": "203.0.113.5",
                            },
                            {
                                "signature_type": "hostname",
                                "signature_value": "host-a.internal",
                            },
                        ],
                    },
                    {
                        "expectation_type": expectation_b,
                        "values": [
                            {
                                "signature_type": "public_ip",
                                "signature_value": "198.51.100.10",
                            },
                        ],
                    },
                ],
            }
        ]
    }


@when(parsers.parse('I call send_signatures for inject_id "{inject_id}"'))
def call_send_signatures(context, inject_id):
    context["inject_id"] = inject_id
    context["send_exception"] = None
    try:
        context["signature_manager"].send_signatures(
            inject_id,
            context["execution_details"],
            context["signatures"],
        )
    except Exception as exc:
        context["send_exception"] = exc


@when("I call resolve_container_ip")
def call_resolve_container_ip(context):
    context["resolve_exception"] = None
    try:
        context["resolved_ip"] = context["signature_manager"].resolve_container_ip()
    except Exception as exc:
        context["resolve_exception"] = exc


@then("send_signatures completes without raising an exception")
def send_signatures_completes_without_exception(context):
    assert context["send_exception"] is None


@then(
    parsers.parse(
        "a POST request is sent to /injects/execution/callback/{inject_id}",
    )
)
def assert_post_request_sent_to_callback(context, inject_id):
    assert context["captured_calls"]
    assert (
        context["captured_calls"][-1]["path"]
        == f"/injects/execution/callback/{inject_id}"
    )


@then("the POST request body contains signatures.targets as a list")
def assert_targets_is_list(context):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    assert isinstance(targets, list)


@then(
    parsers.parse(
        'signatures.targets[0].signature_values[0].expectation_type equals "{expected_value}"'
    )
)
def assert_expectation_type(context, expected_value):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    assert targets[0]["signature_values"][0]["expectation_type"] == expected_value


@then(
    parsers.parse(
        'signatures.targets[0].signature_values[0].values[0].signature_type equals "{expected_value}"'
    )
)
def assert_signature_type(context, expected_value):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    assert (
        targets[0]["signature_values"][0]["values"][0]["signature_type"]
        == expected_value
    )


@then(
    parsers.parse(
        'signatures.targets[0].signature_values[0].values[0].signature_value equals "{expected_value}"'
    )
)
def assert_signature_value(context, expected_value):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    assert (
        targets[0]["signature_values"][0]["values"][0]["signature_value"]
        == expected_value
    )


@then("signatures.targets[0] contains a signature_target key")
def assert_signature_target_key(context):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    assert "signature_target" in targets[0]


@then(
    parsers.parse(
        "the payload is sent as multiple sequential POST requests to /injects/execution/callback/{inject_id}",
    )
)
def assert_payload_sent_as_multiple_chunks(context, inject_id):
    assert context["send_exception"] is None
    assert len(context["captured_calls"]) > 1
    assert all(
        call_item["path"] == f"/injects/execution/callback/{inject_id}"
        for call_item in context["captured_calls"]
    )


@then(
    "each POST request body is a valid self-contained envelope with the same structure as a single-send payload"
)
def assert_each_envelope_is_self_contained(context):
    for call_item in context["captured_calls"]:
        post_data = call_item["post_data"]
        assert "execution_output_structured" in post_data
        targets = _extract_targets(post_data)
        assert isinstance(targets, list)
        assert len(targets) > 0


@then("no POST request body contains chunk_index or total_chunks keys")
def assert_no_chunk_metadata(context):
    for call_item in context["captured_calls"]:
        post_data = call_item["post_data"]
        assert "chunk_index" not in post_data
        assert "total_chunks" not in post_data


@then("the union of targets across all POST requests equals the original target set")
def assert_targets_union_matches_original(context):
    original_targets = context["signatures"]["targets"]
    sent_targets = [
        target
        for call_item in context["captured_calls"]
        for target in _extract_targets(call_item["post_data"])
    ]
    assert len(sent_targets) == len(original_targets), (
        f"Expected {len(original_targets)} targets across all envelopes, "
        f"got {len(sent_targets)}"
    )
    for original, sent in zip(original_targets, sent_targets):
        assert sent["signature_target"] == original["signature_target"]


@then("no individual POST request body exceeds MAX_PAYLOAD_SIZE bytes without warning")
def assert_payload_size_per_chunk(context):
    max_payload_size = context["signature_manager"].max_payload_size
    for call_item in context["captured_calls"]:
        post_data = call_item["post_data"]
        payload_size = len(json.dumps(post_data).encode())
        assert payload_size <= max_payload_size


@then(
    parsers.parse(
        "send_signatures sends a total of {total_requests:d} POST requests to /injects/execution/callback/{inject_id}"
    )
)
def assert_total_post_requests(context, total_requests, inject_id):
    assert len(context["captured_calls"]) == total_requests
    assert all(
        call_item["path"] == f"/injects/execution/callback/{inject_id}"
        for call_item in context["captured_calls"]
    )


@then(
    "a WARNING log message containing the retry attempt number is emitted before each of the 3 retry attempts"
)
def assert_warning_logs_for_retries(context):
    assert context["logger"].warning.call_count == 3
    warning_messages = [
        " ".join(str(arg) for arg in warning_call.args)
        for warning_call in context["logger"].warning.call_args_list
    ]
    assert any("1" in message for message in warning_messages)
    assert any("2" in message for message in warning_messages)
    assert any("3" in message for message in warning_messages)


@then(parsers.parse("the wait before attempt {attempt:d} is {seconds:d} second"))
@then(parsers.parse("the wait before attempt {attempt:d} is {seconds:d} seconds"))
def assert_wait_before_attempt(context, attempt, seconds):
    assert context["sleep_mock"].call_args_list[attempt - 2] == call(seconds)


@then("a SignatureTransmissionError is raised after all retries are exhausted")
def assert_signature_transmission_error_after_retries(context):
    assert isinstance(context["send_exception"], SignatureTransmissionError)


@then(
    parsers.parse(
        "only {request_count:d} POST request is sent to /injects/execution/callback/{inject_id}"
    )
)
def assert_single_post_request(context, request_count, inject_id):
    assert len(context["captured_calls"]) == request_count
    assert (
        context["captured_calls"][0]["path"]
        == f"/injects/execution/callback/{inject_id}"
    )


@then(
    parsers.parse(
        "an ERROR log message containing status code {status_code:d} and the response body is emitted"
    )
)
def assert_error_log_contains_status_and_body(context, status_code):
    assert context["logger"].error.call_count >= 1
    message_text = " ".join(
        str(arg)
        for call_args in context["logger"].error.call_args_list
        for arg in call_args.args
    )
    assert str(status_code) in message_text
    assert context["error_body"] in message_text


@then("an exception is raised immediately")
def assert_exception_raised_immediately(context):
    assert context["send_exception"] is not None


@then("no sleep or wait occurs before the exception is raised")
def assert_no_sleep_occurs(context):
    assert context["sleep_mock"].call_count == 0


@then("the returned value is a non-empty valid IPv4 address string")
def assert_returned_value_valid_ipv4(context):
    assert context["resolve_exception"] is None
    resolved_ip = context["resolved_ip"]
    assert isinstance(resolved_ip, str)
    assert resolved_ip.strip() != ""
    assert ipaddress.ip_address(resolved_ip).version == 4


@then(parsers.parse('the returned value is the string "{expected_value}"'))
def assert_returned_value_matches(context, expected_value):
    assert context["resolved_ip"] == expected_value


@then(parsers.parse("exactly {count:d} WARNING log message is emitted"))
def assert_warning_count(context, count):
    assert context["logger"].warning.call_count == count


@then("no exception propagates from resolve_container_ip")
def assert_no_exception_from_resolve_container_ip(context):
    assert context["resolve_exception"] is None


@then(
    "the POST request body nests signature values under separate expectation_type entries within signatures.targets[0].signature_values"
)
def assert_signature_values_nested_by_expectation_type(context):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    entries = targets[0]["signature_values"]
    expectation_types = {entry["expectation_type"] for entry in entries}
    assert expectation_types == {"DETECTION", "PREVENTION"}


@then(
    'the entry with expectation_type "DETECTION" contains only DETECTION signature values'
)
def assert_detection_values_grouped_correctly(context):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    entries = targets[0]["signature_values"]
    detection_entry = next(
        entry for entry in entries if entry["expectation_type"] == "DETECTION"
    )
    detection_values = {value["signature_value"] for value in detection_entry["values"]}
    assert detection_values == {"203.0.113.5", "host-a.internal"}
    assert "198.51.100.10" not in detection_values


@then(
    'the entry with expectation_type "PREVENTION" contains only PREVENTION signature values'
)
def assert_prevention_values_grouped_correctly(context):
    body = context["captured_calls"][-1]["post_data"]
    targets = _extract_targets(body)
    entries = targets[0]["signature_values"]
    prevention_entry = next(
        entry for entry in entries if entry["expectation_type"] == "PREVENTION"
    )
    prevention_values = {
        value["signature_value"] for value in prevention_entry["values"]
    }
    assert prevention_values == {"198.51.100.10"}
    assert "203.0.113.5" not in prevention_values
    assert "host-a.internal" not in prevention_values
