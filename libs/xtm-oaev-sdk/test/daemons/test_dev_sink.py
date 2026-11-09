"""Tests for the dev sink: where a daemon in dev mode writes what the platform would get.

Feature: Dev sink
  A daemon started with --dev writes every call the platform would have received
  instead of sending it. Each call is checked against what the platform accepts, its
  secrets are redacted, and the calls are written as one readable JSON list, so a run can
  be shared, committed and reviewed in a diff.
"""

import io
import json
import sys
import threading
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

import pytest
import xtm_oaev_sdk as sdk

INJECT = "5dca53ff-8a4f-4c1b-9d5e-0b6f5b6f1a01"
CALLBACK = f"/api/injects/execution/callback/{INJECT}"
SECRET = "s3cr3t-value"


def _given_sink_opener() -> Callable[..., Any]:
    """Given the SDK opens dev sinks"""
    opener = getattr(sdk, "dev_sink", None)
    assert opener is not None, "Expected xtm_oaev_sdk.dev_sink on public surface"
    return opener


def _given_environment_secrets_reader() -> Callable[..., list[str]]:
    """Given the SDK lists the environment's secret values"""
    reader = getattr(sdk, "environment_secret_values", None)
    assert reader is not None, "Expected xtm_oaev_sdk.environment_secret_values"
    return reader


def _given_out(tmp_path: Path) -> Path:
    """Given an output file "run.json" """
    return tmp_path / "run.json"


def _given_callback(**overrides: Any) -> dict[str, Any]:
    """Given an execution callback as an injector sends it"""
    body: dict[str, Any] = {
        "execution_message": "Scan done",
        "execution_status": "SUCCESS",
        "execution_action": "complete",
    }
    body.update(overrides)
    return body


def _when_recording(sink: Any, *calls: tuple[str, str, Any]) -> Exception | None:
    """When the calls are recorded"""
    try:
        for method, path, body in calls:
            sink.record(method, path, body)
    except Exception as error:  # pylint: disable=broad-except
        return error
    return None


def _when_closing(sink: Any) -> None:
    """When the sink is closed"""
    sink.close()


def _then_written(out: Path) -> Any:
    """Then the output is one JSON document"""
    return json.loads(out.read_text(encoding="utf-8"))


def _then_text_excludes(text: str, value: str) -> None:
    """Then the text never holds "<value>" """
    assert value not in text, f"Expected {value!r} to be redacted from {text!r}"


def _then_text_includes(text: str, value: str) -> None:
    """Then the text holds "<value>" """
    assert value in text, f"Expected {value!r} in {text!r}"


def _then_refused_with_400(error: Exception | None) -> None:
    """Then the call is refused the way the platform answers it, with a 400"""
    assert isinstance(error, sdk.OpenAEVHttpError), f"Expected a 400, got {error!r}"
    assert error.response_code == 400


@pytest.mark.parametrize(
    "body",
    [
        _given_callback(execution_message=f"key {SECRET} refused"),
        _given_callback(
            execution_output_structured=json.dumps({"auth": {"value": SECRET}})
        ),
        _given_callback(
            execution_output_structured=json.dumps({"raw": f'say "{SECRET}"'})
        ),
    ],
    ids=["free text", "nested JSON text", "escaped inside JSON text"],
)
def test_a_secret_is_masked_wherever_it_appears(tmp_path: Path, body: Any) -> None:
    """It replaces a secret with *** wherever it appears in a recorded body.

    Scenario Outline: A secret is masked wherever it appears
      Given the SDK opens dev sinks
      And an output file "run.json"
      When an execution callback holding the secret in <location> is recorded
      And the sink is closed
      Then the text never holds the secret
      And the text holds "***"
    """
    opener = _given_sink_opener()
    out = _given_out(tmp_path)
    sink = opener(out=str(out), secrets=[SECRET])
    _when_recording(sink, ("POST", CALLBACK, body))
    _when_closing(sink)
    text = out.read_text(encoding="utf-8")
    _then_text_excludes(text, SECRET)
    _then_text_includes(text, "***")


def test_kept_keys_and_paths_are_never_rewritten(tmp_path: Path) -> None:
    """It never rewrites the path, nor the keys the daemon keeps, even equal to a secret.

    Scenario: Kept keys and paths are never rewritten
      Given the SDK opens dev sinks
      And an output file "run.json"
      And a secret equal to the inject id and to "SUCCESS"
      When an execution callback is recorded with execution_status kept
      And the sink is closed
      Then the path and the execution_status are written unchanged
    """
    opener = _given_sink_opener()
    out = _given_out(tmp_path)
    sink = opener(out=str(out), secrets=[INJECT, "SUCCESS"], keep=["execution_status"])
    _when_recording(sink, ("POST", CALLBACK, _given_callback()))
    _when_closing(sink)
    call = _then_written(out)[0]
    assert (call["path"], call["body"]["execution_status"]) == (CALLBACK, "SUCCESS")


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", CALLBACK, _given_callback(unknown_key=1)),
        ("POST", CALLBACK, _given_callback(execution_status="DONE")),
        (
            "PUT",
            "/api/injects/expectations/4e5d",
            {"result": "Detected", "is_success": True},
        ),
        (
            "POST",
            "/api/inject-expectations-traces/bulk",
            {"expectation_traces": [{"inject_expectation_trace_expectation": "4e5d"}]},
        ),
    ],
    ids=["unknown key", "unknown status", "update without collector", "bad trace"],
)
def test_a_body_the_platform_would_reject_is_refused(
    tmp_path: Path, method: str, path: str, body: Any
) -> None:
    """It refuses a body the platform would reject, with a 400, and writes nothing.

    Scenario Outline: A body the platform would reject is refused
      Given the SDK opens dev sinks
      And an output file "run.json"
      When a <call> the platform would reject is recorded
      Then the call is refused the way the platform answers it, with a 400
      And the output is an empty JSON list
    """
    opener = _given_sink_opener()
    out = _given_out(tmp_path)
    sink = opener(out=str(out), secrets=[])
    error = _when_recording(sink, (method, path, body))
    _when_closing(sink)
    _then_refused_with_400(error)
    assert _then_written(out) == []


def test_the_output_is_one_pretty_printed_json_list(tmp_path: Path) -> None:
    """It writes the calls as one indented JSON list, keys in the payload's order.

    Scenario: The output is one pretty-printed JSON list
      Given the SDK opens dev sinks
      And an output file "run.json"
      When a reception and an execution callback are recorded
      And the sink is closed
      Then the output is one JSON list, indented by 2, one key per line
      And the body keys follow the platform payload's field order
    """
    opener = _given_sink_opener()
    out = _given_out(tmp_path)
    sink = opener(out=str(out), secrets=[])
    _when_recording(
        sink,
        (
            "POST",
            f"/api/injects/execution/reception/{INJECT}",
            {"tracking_total_count": 1},
        ),
        (
            "POST",
            CALLBACK,
            {
                "execution_action": "complete",
                "execution_status": "SUCCESS",
                "execution_message": "Scan done",
            },
        ),
    )
    _when_closing(sink)
    calls = _then_written(out)
    text = out.read_text(encoding="utf-8")
    assert text == json.dumps(calls, indent=2, ensure_ascii=False) + "\n"
    assert list(calls[1]["body"]) == [
        "execution_message",
        "execution_status",
        "execution_action",
    ]


def test_two_runs_differing_by_one_field_differ_on_that_line_only(
    tmp_path: Path,
) -> None:
    """It writes one key per line, so runs differing by one field differ by one line.

    Scenario: Two runs differing by one field diff on that line only
      Given the SDK opens dev sinks
      And two runs whose execution_message differ
      When their outputs are compared line by line
      Then only the execution_message line differs
    """
    opener = _given_sink_opener()
    texts = []
    for message in ("Scan done", "Scan failed"):
        out = tmp_path / f"{message}.json"
        sink = opener(out=str(out), secrets=[])
        _when_recording(
            sink, ("POST", CALLBACK, _given_callback(execution_message=message))
        )
        _when_closing(sink)
        texts.append(out.read_text(encoding="utf-8").splitlines())
    differing = [a for a, b in zip(*texts) if a != b]
    assert len(texts[0]) == len(texts[1])
    assert differing == ['      "execution_message": "Scan done",']


def test_an_interrupted_run_leaves_valid_json(tmp_path: Path) -> None:
    """It keeps the output a valid JSON list after each call, before any close.

    Scenario: An interrupted run leaves valid JSON
      Given the SDK opens dev sinks
      And an output file "run.json"
      When an execution callback is recorded
      And the run is interrupted before the sink is closed
      Then the output is a valid JSON list holding that call
    """
    opener = _given_sink_opener()
    out = _given_out(tmp_path)
    sink = opener(out=str(out), secrets=[])
    _when_recording(sink, ("POST", CALLBACK, _given_callback()))
    assert [call["path"] for call in _then_written(out)] == [CALLBACK]


def test_without_out_the_list_goes_to_stdout_at_the_end() -> None:
    """It writes the list on stdout once, when the sink closes.

    Scenario: Without an output file, the list goes to stdout at the end
      Given the SDK opens dev sinks
      When an execution callback is recorded without an output file
      Then nothing is written on stdout before the sink is closed
      And stdout holds the JSON list once the sink is closed
    """
    opener = _given_sink_opener()
    stdout = io.StringIO()
    with patch.object(sys, "stdout", stdout):
        sink = opener(secrets=[])
        _when_recording(sink, ("POST", CALLBACK, _given_callback()))
        before = stdout.getvalue()
        _when_closing(sink)
    assert before == ""
    assert [call["path"] for call in json.loads(stdout.getvalue())] == [CALLBACK]


def test_the_list_can_go_to_stderr() -> None:
    """It writes the list on stderr when asked, leaving stdout to the daemon.

    Scenario: The list can go to stderr
      Given the SDK opens dev sinks
      When an execution callback is recorded to stderr
      And the sink is closed
      Then stderr holds the JSON list and stdout holds nothing
    """
    opener = _given_sink_opener()
    stdout, stderr = io.StringIO(), io.StringIO()
    with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
        sink = opener(secrets=[], to_stderr=True)
        _when_recording(sink, ("POST", CALLBACK, _given_callback()))
        _when_closing(sink)
    assert stdout.getvalue() == ""
    assert json.loads(stderr.getvalue())[0]["path"] == CALLBACK


def test_the_calls_recorded_stay_available_unredacted(tmp_path: Path) -> None:
    """It keeps the calls as recorded, for the run to read, while it writes them redacted.

    Scenario: The calls recorded stay available, unredacted
      Given the SDK opens dev sinks
      When an execution callback holding a secret is recorded
      Then the sink's calls hold the callback as recorded
    """
    opener = _given_sink_opener()
    sink = opener(out=str(_given_out(tmp_path)), secrets=[SECRET])
    body = _given_callback(execution_message=SECRET)
    _when_recording(sink, ("POST", CALLBACK, body))
    assert sink.calls == [{"method": "POST", "path": CALLBACK, "body": body}]


def test_a_refusal_says_why_on_stderr_and_returns_2() -> None:
    """It says why a run is refused on stderr, secrets redacted, and returns 2.

    Scenario: A refusal says why on stderr and returns 2
      Given the SDK opens dev sinks
      When a run is refused because "bad key s3cr3t-value"
      Then stderr says "dev: refused: bad key ***"
      And the exit code is 2
    """
    opener = _given_sink_opener()
    stderr = io.StringIO()
    with patch.object(sys, "stderr", stderr):
        code = opener(secrets=[SECRET]).refuse(f"bad key {SECRET}")
    assert stderr.getvalue() == "dev: refused: bad key ***\n"
    assert code == 2


def test_a_note_goes_to_stderr_redacted() -> None:
    """It writes a note on stderr, prefixed with "dev:", secrets redacted.

    Scenario: A note goes to stderr, redacted
      Given the SDK opens dev sinks
      When the sink notes "token s3cr3t-value dropped"
      Then stderr says "dev: token *** dropped"
    """
    opener = _given_sink_opener()
    stderr = io.StringIO()
    with patch.object(sys, "stderr", stderr):
        opener(secrets=[SECRET]).note(f"token {SECRET} dropped")
    assert stderr.getvalue() == "dev: token *** dropped\n"


def test_environment_secrets_are_the_values_of_secret_named_variables() -> None:
    """It lists the values of the environment variables whose name says secret.

    Scenario: Environment secrets are the values of secret-named variables
      Given the SDK lists the environment's secret values
      When the environment holds SHODAN_API_KEY, OPENAEV_TOKEN, a short SPLUNK_PASSWORD and HOME
      Then the secret values are the API key and the token only
    """
    reader = _given_environment_secrets_reader()
    environ = {
        "SHODAN_API_KEY": "shodan-key-1",
        "OPENAEV_TOKEN": "platform-token",
        "SPLUNK_PASSWORD": "abc",
        "HOME": "/home/dev",
    }
    assert set(reader(environ)) == {"shodan-key-1", "platform-token"}


def test_a_run_waits_for_a_call_recorded_from_another_thread(tmp_path: Path) -> None:
    """It wakes a run waiting for a call as soon as another thread records it.

    Scenario: A run waits for a call recorded from another thread
      Given the SDK opens dev sinks
      When a thread records the complete callback while the run waits for it
      Then the wait ends with the call found
    """
    opener = _given_sink_opener()
    sink = opener(out=str(_given_out(tmp_path)), secrets=[])
    worker = threading.Timer(
        0.05, sink.record, args=("POST", CALLBACK, _given_callback())
    )
    worker.start()
    found = sink.wait_for(
        lambda calls: any(call["path"] == CALLBACK for call in calls), timeout=5
    )
    worker.join()
    assert found is True


def test_a_wait_gives_up_after_its_timeout(tmp_path: Path) -> None:
    """It stops waiting after the timeout when no call satisfies the condition.

    Scenario: A wait gives up after its timeout
      Given the SDK opens dev sinks
      When the run waits 0.1 second for a call nobody records
      Then the wait ends with no call found
    """
    opener = _given_sink_opener()
    sink = opener(out=str(_given_out(tmp_path)), secrets=[])
    assert sink.wait_for(lambda calls: bool(calls), timeout=0.1) is False
