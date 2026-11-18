"""Tests for the call tape: record a daemon's outside calls, replay them offline.

Feature: Record and replay the outside calls of a daemon
  A daemon calls the outside world over HTTP (a security product's API) and through
  commands (a scanner binary). Recording writes every call and its answer to a tape:
  one readable JSON document, a header then the calls, meant to be committed and
  reviewed in a diff. Replaying answers each call from the tape, so the daemon runs
  offline. A call the tape does not hold fails, naming it, and never reaches the
  network, whatever client makes it. Secrets are kept out of the tape, replay still
  finds a call whatever key it carries, and a lint finds what looks like a secret left.
"""

import gzip
import http.server
import json
import socket
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path
from typing import Any, Iterator, NamedTuple

import pytest
import xtm_oaev_sdk as sdk
from pydantic import TypeAdapter

SECRET = "s3cr3t-key-42"


class Answer(NamedTuple):
    status: Any
    body: bytes


class _ProductApi(http.server.BaseHTTPRequestHandler):
    """A security product's API: answers with what it was asked, and counts calls."""

    calls = 0

    def log_message(self, *_: Any) -> None:
        pass

    def _answer(self) -> None:
        type(self).calls += 1
        length = int(self.headers.get("Content-Length") or 0)
        sent = self.rfile.read(length).decode() if length else ""
        if self.path.startswith("/gzip"):
            body = gzip.compress(b"compressed answer")
            self.send_response(200)
            self.send_header("Content-Encoding", "gzip")
        else:
            body = json.dumps(
                {"path": self.path, "sent": sent, "call": type(self).calls}
            ).encode()
            self.send_response(201 if self.command == "POST" else 200)
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_GET = _answer
    do_POST = _answer


class ProductApi:
    """A security product's API running locally, which a test can shut down."""

    def __init__(self) -> None:
        _ProductApi.calls = 0
        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _ProductApi)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self._server.server_address[1]}"
        self.running = True

    def shut_down(self) -> None:
        if self.running:
            self._server.shutdown()
            self._server.server_close()
            self.running = False


@pytest.fixture
def product_api() -> Iterator[ProductApi]:
    api = ProductApi()
    yield api
    api.shut_down()


def _given_call_tape(path: Path, mode: str, *secrets: str) -> Any:
    """Given a call tape of the "Lab SIEM" daemon in "<mode>" mode on tape.json,
    knowing <secrets>"""
    tape_class = getattr(sdk, "CallTape", None)
    assert tape_class is not None, "Expected xtm_oaev_sdk.CallTape on public surface"
    return tape_class(str(path), mode, secrets=list(secrets), daemon="Lab SIEM")


def _given_recorded(path: Path, *calls: tuple, secrets: tuple = ()) -> list:
    """Given the connector made <calls> while a tape recorded them"""
    return _when_calling_with(_given_call_tape(path, "record", *secrets), *calls)


def _given_recorded_commands(path: Path, *commands: list[str]) -> list:
    """Given the connector ran <commands> while a tape recorded them"""
    return _when_running_commands_with(_given_call_tape(path, "record"), *commands)


def _given_the_api_shut_down(api: ProductApi) -> None:
    """Given the product's API is shut down: nothing answers on its URL any more"""
    api.shut_down()
    _ProductApi.calls = 0


def _given_tape_holding(path: Path, *calls: Any, version: str = "1") -> None:
    """Given a tape file of tape version <version> holding <calls>"""
    document = {
        "tape_version": version,
        "sdk_version": sdk.__version__,
        "daemon": "Lab SIEM",
        "recorded_at": "2026-11-10T08:00:00Z",
        "calls": [call.model_dump(mode="json", exclude_none=True) for call in calls],
    }
    path.write_text(json.dumps(document, indent=2) + "\n")


def _call(url: str, body: str | None = None, headers: dict | None = None) -> Answer:
    request = urllib.request.Request(
        url, data=body.encode() if body is not None else None, headers=headers or {}
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return Answer(response.status, response.read())
    except Exception as error:  # noqa: BLE001
        return Answer(error, b"")


def _when_calling_with(tape: Any, *calls: tuple) -> list[Answer]:
    """When the connector makes <calls> while the tape runs"""
    tape.start()
    try:
        return [_call(*call) for call in calls]
    finally:
        tape.stop()


def _when_calling_with_requests(tape: Any, url: str) -> Any:
    """When the connector makes a GET with requests while the tape runs"""
    requests = pytest.importorskip("requests")
    tape.start()
    try:
        return requests.get(url, timeout=5).json()
    finally:
        tape.stop()


def _when_running_commands_with(tape: Any, *commands: list[str], **kwargs: Any) -> list:
    """When the connector runs <commands> while the tape runs"""
    tape.start()
    try:
        results = []
        for argv in commands:
            try:
                results.append(subprocess.run(argv, capture_output=True, **kwargs))
            except Exception as error:  # noqa: BLE001
                results.append(error)
        return results
    finally:
        tape.stop()


def _when_calling_without_a_tape(url: str) -> Answer:
    """When the connector makes a GET with no tape running"""
    return _call(url)


def _when_making_a_tape(path: Path, mode: str) -> Any:
    """When a call tape is made in "<mode>" mode"""
    tape_class = getattr(sdk, "CallTape", None)
    assert tape_class is not None, "Expected xtm_oaev_sdk.CallTape on public surface"
    try:
        return tape_class(str(path), mode)
    except Exception as error:  # noqa: BLE001
        return error


def _then_statuses_are(answers: list[Answer], *statuses: int) -> None:
    """Then the connector gets the statuses <statuses>"""
    assert [a.status for a in answers] == list(statuses), f"Got {answers}"


def _then_answers_are(answers: list[Answer], expected: list[Answer]) -> None:
    """Then the connector gets exactly the answers it got when recording"""
    assert answers == expected


def _then_answer_calls_are(answers: list[Answer], *calls: int) -> None:
    """Then the answers are those of the API's calls <calls>, in that order"""
    assert [json.loads(a.body)["call"] for a in answers] == list(calls)


def _then_answer_decompresses_to(answer: Answer, text: bytes) -> None:
    """Then the answer's bytes decompress to "<text>" """
    assert gzip.decompress(answer.body) == text


def _then_api_was_called(times: int) -> None:
    """Then the product's API was called <times> time(s)"""
    assert _ProductApi.calls == times


def _then_tape_holds(path: Path, count: int) -> None:
    """Then the tape is a tape document holding <count> call(s)"""
    document = json.loads(path.read_text())
    tape = TypeAdapter(sdk.Tape).validate_python(document)
    assert len(tape.calls) == count, f"Expected {count} calls on the tape: {document}"


def _then_tape_excludes(path: Path, secret: str) -> None:
    """Then "<secret>" appears nowhere on the tape"""
    text = path.read_text()
    assert text.strip(), "Expected something on the tape"
    assert secret not in text


def _then_fails_naming(failure: Any, *parts: str) -> None:
    """Then it fails with an error naming <parts>"""
    error = failure.status if isinstance(failure, Answer) else failure
    assert isinstance(error, Exception), f"Expected a failure, got {failure!r}"
    text = repr(error) + str(getattr(error, "reason", ""))
    for part in parts:
        assert part in text, f"Expected {part!r} in {text!r}"


def _then_command_gave(result: Any, returncode: int, stdout: bytes) -> None:
    """Then the command gives exit code <returncode> and "<stdout>" """
    assert not isinstance(result, Exception), f"Expected a result, got {result!r}"
    assert (result.returncode, result.stdout) == (returncode, stdout)


def _then_command_did_not_run(marker: Path) -> None:
    """Then the command did not run: its marker file is not created again"""
    assert not marker.exists()


def _then_command_failed_with(result: Any, returncode: int) -> None:
    """Then it raises a CalledProcessError with exit code <returncode>"""
    assert isinstance(result, subprocess.CalledProcessError), f"Got {result!r}"
    assert result.returncode == returncode


def _then_same_json(replayed: Any, recorded: Any) -> None:
    """Then the connector gets the same JSON it got when recording"""
    assert replayed == recorded


def _then_refused(made: Any) -> None:
    """Then it is refused"""
    assert isinstance(made, ValueError), f"Expected a refusal, got {made!r}"


def test_recording_answers_the_connector_and_writes_the_calls(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It lets recorded calls through to the API, and writes each call and its answer.

    Scenario: Recording answers the connector and writes the calls
      Given a security product's API, running locally
      And a call tape in "record" mode on tape.json
      When the connector makes a GET and a POST while the tape runs
      Then the connector gets the statuses 200 and 201
      And the product's API was called 2 time(s)
      And the tape holds 2 call(s), each one a call the SDK models
    """
    path = tmp_path / "tape.json"
    tape = _given_call_tape(path, "record")
    answers = _when_calling_with(
        tape, (f"{product_api.url}/alerts?q=scan",), (f"{product_api.url}/search", "q")
    )
    _then_statuses_are(answers, 200, 201)
    _then_api_was_called(2)
    _then_tape_holds(path, 2)


def test_replaying_answers_offline_from_the_tape(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It answers recorded calls from the tape, with the API shut down.

    Scenario: Replaying answers offline from the tape
      Given the connector made a GET and a POST while a tape recorded them
      And the product's API is shut down: nothing answers on its URL any more
      And a call tape in "replay" mode on tape.json
      When the connector makes the same calls while the tape runs
      Then the connector gets exactly the answers it got when recording
    """
    path = tmp_path / "tape.json"
    calls = ((f"{product_api.url}/alerts?q=scan",), (f"{product_api.url}/search", "q"))
    recorded = _given_recorded(path, *calls)
    _given_the_api_shut_down(product_api)
    tape = _given_call_tape(path, "replay")
    answers = _when_calling_with(tape, *calls)
    _then_answers_are(answers, recorded)


def test_identical_calls_replay_in_recorded_order_then_repeat_the_last(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It answers identical calls in the order recorded, then repeats the last answer.

    Scenario: Identical calls replay in recorded order, then repeat the last
      Given the connector made the same GET twice while a tape recorded them
      And the product's API is shut down: nothing answers on its URL any more
      And a call tape in "replay" mode on tape.json
      When the connector makes that GET three times while the tape runs
      Then the answers are those of the API's calls 1, 2 and 2, in that order
    """
    path = tmp_path / "tape.json"
    url = f"{product_api.url}/poll"
    _given_recorded(path, (url,), (url,))
    _given_the_api_shut_down(product_api)
    tape = _given_call_tape(path, "replay")
    answers = _when_calling_with(tape, (url,), (url,), (url,))
    _then_answer_calls_are(answers, 1, 2, 2)


def test_a_compressed_answer_is_taped_and_replayed_decompressed(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It tapes a compressed answer decompressed, readable, and replays it so.

    Scenario: A compressed answer is taped and replayed decompressed
      Given the daemon made a GET of <api>/gzip while a tape recorded it
      And the product's API is shut down: nothing answers on its URL any more
      And a call tape of the "Lab SIEM" daemon in "replay" mode on tape.json
      When the daemon makes the GET of <api>/gzip while the tape runs
      Then the tape holds the answer as the text "compressed answer", noted as gzip
      And the daemon gets "compressed answer", without the Content-Encoding header
    """
    path = tmp_path / "tape.json"
    url = f"{product_api.url}/gzip"
    recorded = _given_recorded(path, (url,))
    _given_the_api_shut_down(product_api)
    tape = _given_call_tape(path, "replay")
    answers = _when_calling_with(tape, (url,))
    _then_answer_decompresses_to(recorded[0], b"compressed answer")
    response = json.loads(path.read_text())["calls"][0]["response"]
    assert response["body"] == {"text": "compressed answer"}
    assert response["decoded_from"] == "gzip"
    assert answers == [Answer(200, b"compressed answer")]


def test_requests_calls_record_and_replay(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It records and replays the calls made with requests, as most connectors do.

    Scenario: Calls made with requests record and replay
      Given the connector made a GET with requests while a tape recorded it
      And the product's API is shut down: nothing answers on its URL any more
      And a call tape in "replay" mode on tape.json
      When the connector makes a GET with requests while the tape runs
      Then the connector gets the same JSON it got when recording
    """
    path = tmp_path / "tape.json"
    url = f"{product_api.url}/alerts?q=scan"
    recorded = _when_calling_with_requests(_given_call_tape(path, "record"), url)
    _given_the_api_shut_down(product_api)
    tape = _given_call_tape(path, "replay")
    replayed = _when_calling_with_requests(tape, url)
    _then_same_json(replayed, recorded)


def test_https_calls_replay_without_any_network(tmp_path: Path) -> None:
    """It replays an HTTPS call from a tape, with no network and no TLS at all.

    Scenario: HTTPS calls replay without any network
      Given a tape file holding a GET to https://product.invalid/v1/alerts answered 200 "[]"
      And a call tape in "replay" mode on tape.json
      When the connector makes that GET while the tape runs
      Then the connector gets exactly the answers 200 "[]"
    """
    path = tmp_path / "tape.json"
    _given_tape_holding(
        path,
        sdk.TapedHttpCall(
            request=sdk.TapedHttpRequest(
                method="GET", url="https://product.invalid/v1/alerts", headers=[]
            ),
            response=sdk.TapedHttpResponse(
                status=200,
                reason="OK",
                headers=[["Content-Type", "application/json"]],
                body=sdk.TapedBody(text="[]"),
            ),
        ),
    )
    tape = _given_call_tape(path, "replay")
    answers = _when_calling_with(tape, ("https://product.invalid/v1/alerts",))
    _then_answers_are(answers, [Answer(200, b"[]")])


def test_commands_replay_without_running(tmp_path: Path) -> None:
    """It replays a recorded command's result without running the command again.

    Scenario: Commands replay without running
      Given the connector ran a command printing "scan done" and leaving a marker file while a tape recorded it
      And the marker file is removed
      And a call tape in "replay" mode on tape.json
      When the connector runs the same command while the tape runs
      Then the command gives exit code 0 and "scan done"
      And the command did not run: its marker file is not created again
    """
    marker = tmp_path / "ran"
    script = (
        f"import pathlib; pathlib.Path({str(marker)!r}).touch(); print('scan done')"
    )
    argv = [sys.executable, "-c", script]
    path = tmp_path / "tape.json"
    _given_recorded_commands(path, argv)
    marker.unlink()
    tape = _given_call_tape(path, "replay")
    results = _when_running_commands_with(tape, argv)
    _then_command_gave(results[0], 0, b"scan done\n")
    _then_command_did_not_run(marker)


def test_a_failed_command_replays_its_failure(tmp_path: Path) -> None:
    """It replays a failed command, raising as subprocess.run does with check=True.

    Scenario: A failed command replays its failure
      Given the connector ran a command exiting with code 3 while a tape recorded it
      And a call tape in "replay" mode on tape.json
      When the connector runs it with check=True while the tape runs
      Then it raises a CalledProcessError with exit code 3
    """
    argv = [sys.executable, "-c", "import sys; sys.exit(3)"]
    path = tmp_path / "tape.json"
    _given_recorded_commands(path, argv)
    tape = _given_call_tape(path, "replay")
    results = _when_running_commands_with(tape, argv, check=True)
    _then_command_failed_with(results[0], 3)


# ---- Constraints identified ----


def test_an_unrecorded_call_fails_and_stays_offline(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It fails a call the tape does not hold, naming it, without reaching the API.

    Scenario: An unrecorded call fails and stays offline
      Given the connector made a GET to /alerts while a tape recorded it
      And a call tape in "replay" mode on tape.json
      When the connector makes a GET to /assets while the tape runs
      Then it fails with an error naming "not on the replay tape" and "/assets"
      And the product's API was called 1 time(s)
    """
    path = tmp_path / "tape.json"
    _given_recorded(path, (f"{product_api.url}/alerts",))
    tape = _given_call_tape(path, "replay")
    answers = _when_calling_with(tape, (f"{product_api.url}/assets",))
    _then_fails_naming(answers[0], "not on the replay tape", "/assets")
    _then_api_was_called(1)


def test_an_unrecorded_command_fails_without_running(tmp_path: Path) -> None:
    """It fails a command the tape does not hold, naming it, without running it.

    Scenario: An unrecorded command fails without running
      Given a tape file holding no call
      And a call tape in "replay" mode on tape.json
      When the connector runs a command while the tape runs
      Then it fails with an error naming "not on the replay tape"
    """
    path = tmp_path / "tape.json"
    _given_tape_holding(path)
    tape = _given_call_tape(path, "replay")
    results = _when_running_commands_with(tape, [sys.executable, "-c", "print(1)"])
    _then_fails_naming(results[0], "not on the replay tape")


def test_secrets_stay_off_the_tape_and_replay_still_matches(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It keeps secrets off the tape, and replays a call whatever key it carries.

    Scenario: Secrets stay off the tape, and replay still matches
      Given the connector made a POST with ?key=s3cr3t-key-42, an Authorization header, an X-Api-Key header and the key in its body, while a tape knowing "s3cr3t-key-42" recorded it
      And the product's API is shut down: nothing answers on its URL any more
      And a call tape in "replay" mode on tape.json, knowing "other-key-99"
      When the connector makes the same POST with "other-key-99" while the tape runs
      Then "s3cr3t-key-42" appears nowhere on the tape
      And the connector gets the statuses 201
    """
    path = tmp_path / "tape.json"

    def call(key: str) -> tuple:
        return (
            f"{product_api.url}/search?key={key}",
            f"token={key}",
            {"Authorization": f"Bearer {key}", "X-Api-Key": key},
        )

    _given_recorded(path, call(SECRET), secrets=(SECRET,))
    _given_the_api_shut_down(product_api)
    tape = _given_call_tape(path, "replay", "other-key-99")
    answers = _when_calling_with(tape, call("other-key-99"))
    _then_tape_excludes(path, SECRET)
    _then_statuses_are(answers, 201)


def test_stopping_the_tape_restores_the_network(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It lets calls reach the network again once the tape is stopped.

    Scenario: Stopping the tape restores the network
      Given a tape file holding no call
      And a call tape in "replay" mode on tape.json, started then stopped
      When the connector makes a GET with no tape running
      Then the connector gets the statuses 200
    """
    path = tmp_path / "tape.json"
    _given_tape_holding(path)
    _when_calling_with(_given_call_tape(path, "replay"))
    answer = _when_calling_without_a_tape(f"{product_api.url}/alerts")
    _then_statuses_are([answer], 200)


def test_an_unknown_mode_is_refused(tmp_path: Path) -> None:
    """It refuses a mode other than record or replay.

    Scenario: An unknown mode is refused
      When a call tape is made in "rewind" mode
      Then it is refused
    """
    made = _when_making_a_tape(tmp_path / "tape.json", "rewind")
    _then_refused(made)


# ---- The tape document ----


def test_the_tape_is_one_readable_json_document_with_a_header(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It writes the tape as one indented JSON document: a header, then the calls.

    Scenario: The tape is one readable JSON document with a header
      Given a call tape of the "Lab SIEM" daemon in "record" mode on tape.json
      When the daemon makes a GET of <api>/alerts while the tape runs
      Then the tape is one JSON document, indented by 2
      And its header names tape version "1", the SDK version, the daemon "Lab SIEM" and when it was recorded
    """
    path = tmp_path / "tape.json"
    _when_calling_with(_given_call_tape(path, "record"), (f"{product_api.url}/alerts",))
    text = path.read_text()
    document = json.loads(text)
    assert text == json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    header = {key: value for key, value in document.items() if key != "calls"}
    assert set(header) == {"tape_version", "sdk_version", "daemon", "recorded_at"}
    assert (header["tape_version"], header["sdk_version"], header["daemon"]) == (
        "1",
        sdk.__version__,
        "Lab SIEM",
    )


def test_json_bodies_are_taped_as_json(tmp_path: Path, product_api: ProductApi) -> None:
    """It keeps a JSON body as JSON on the tape, not as escaped text.

    Scenario: JSON bodies are taped as JSON
      Given a call tape of the "Lab SIEM" daemon in "record" mode on tape.json
      When the daemon POSTs {"query": "scan"} to <api>/search while the tape runs
      Then the request body on the tape is the JSON object {"query": "scan"}
      And the response body on the tape is a JSON object
    """
    path = tmp_path / "tape.json"
    _when_calling_with(
        _given_call_tape(path, "record"),
        (f"{product_api.url}/search", '{"query": "scan"}'),
    )
    call = json.loads(path.read_text())["calls"][0]
    assert call["request"]["body"] == {"json": {"query": "scan"}}
    assert isinstance(call["response"]["body"]["json"], dict)


def test_replay_matches_a_json_body_by_value(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It finds a call whose JSON body has the same value, however it is spaced.

    Scenario: Replay matches a JSON body by value
      Given the daemon POSTed {"query": "scan"} to <api>/search while a tape recorded it
      And the product's API is shut down: nothing answers on its URL any more
      And a call tape of the "Lab SIEM" daemon in "replay" mode on tape.json
      When the daemon POSTs {"query":"scan"} to <api>/search while the tape runs
      Then the daemon gets the statuses 201
    """
    path = tmp_path / "tape.json"
    _given_recorded(path, (f"{product_api.url}/search", '{"query": "scan"}'))
    _given_the_api_shut_down(product_api)
    tape = _given_call_tape(path, "replay")
    answers = _when_calling_with(
        tape, (f"{product_api.url}/search", '{"query":"scan"}')
    )
    _then_statuses_are(answers, 201)


def test_the_tape_is_valid_json_after_each_call(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It rewrites the tape after each call, so it is valid JSON before any stop.

    Scenario: The tape is valid JSON after each call
      Given a call tape of the "Lab SIEM" daemon in "record" mode on tape.json
      When the daemon makes a GET of <api>/alerts and the tape is never stopped
      Then the tape is a tape document holding 1 call(s)
    """
    path = tmp_path / "tape.json"
    tape = _given_call_tape(path, "record")
    tape.start()
    try:
        _call(f"{product_api.url}/alerts")
        _then_tape_holds(path, 1)
    finally:
        tape.stop()


def test_any_other_outbound_socket_fails_closed_on_replay(
    tmp_path: Path, product_api: ProductApi
) -> None:
    """It fails any outbound connection on replay, even from a client it does not tape.

    Scenario: Any other outbound socket fails closed on replay
      Given a tape file of tape version "1" holding no call
      And a call tape of the "Lab SIEM" daemon in "replay" mode on tape.json
      When the daemon opens a raw socket to the product's API while the tape runs
      Then it fails with an error naming "not on the replay tape" and the address
      And the product's API was called 0 time(s)
    """
    path = tmp_path / "tape.json"
    _given_tape_holding(path)
    host, port = product_api.url.removeprefix("http://").split(":")
    tape = _given_call_tape(path, "replay")
    tape.start()
    try:
        with pytest.raises(sdk.TapeMissError) as raised:
            socket.create_connection((host, int(port)), timeout=5)
    finally:
        tape.stop()
    _then_fails_naming(raised.value, "not on the replay tape", port)
    _then_api_was_called(0)


@pytest.mark.parametrize(
    ("content", "reason"),
    [
        ("calls: []", "not a JSON tape"),
        (
            json.dumps(
                {
                    "tape_version": "9",
                    "sdk_version": "0.1.0",
                    "daemon": "x",
                    "recorded_at": "2026-11-10T08:00:00Z",
                    "calls": [],
                }
            ),
            "unsupported tape version",
        ),
        (
            json.dumps(
                {
                    "tape_version": "1",
                    "sdk_version": "0.1.0",
                    "daemon": "x",
                    "recorded_at": "2026-11-10T08:00:00Z",
                    "calls": [{"kind": "ftp"}],
                }
            ),
            "calls[0] is not a taped call",
        ),
    ],
    ids=["not JSON", "unknown version", "not a taped call"],
)
def test_a_tape_that_cannot_be_replayed_is_refused(
    tmp_path: Path, content: str, reason: str
) -> None:
    """It refuses to replay a tape it cannot read, saying why.

    Scenario Outline: A tape that cannot be replayed is refused
      Given a tape file holding <content>
      When a call tape of the "Lab SIEM" daemon in "replay" mode starts on it
      Then it fails with an error naming "<reason>"
    """
    path = tmp_path / "tape.json"
    path.write_text(content)
    tape = _given_call_tape(path, "replay")
    with pytest.raises(sdk.OpenAEVError) as raised:
        tape.start()
    tape.stop()
    _then_fails_naming(raised.value, reason)


# ---- Tape lint ----


def _given_lint() -> Any:
    """Given the SDK lints tapes for secrets left on them"""
    lint = getattr(sdk, "lint_tape", None)
    assert lint is not None, "Expected xtm_oaev_sdk.lint_tape on public surface"
    return lint


def test_a_recorded_tape_lints_clean(tmp_path: Path, product_api: ProductApi) -> None:
    """It finds nothing on a tape recorded with its secrets redacted.

    Scenario: A recorded tape lints clean
      Given the daemon called <api>/search with its key, header and token, a tape recording them
      When the tape is linted, knowing the key
      Then the lint finds nothing
    """
    path = tmp_path / "tape.json"
    _given_recorded(
        path,
        (
            f"{product_api.url}/search?key={SECRET}",
            f"token={SECRET}",
            {"Authorization": f"Bearer {SECRET}"},
        ),
        secrets=(SECRET,),
    )
    assert _given_lint()(str(path), secrets=[SECRET]) == []


@pytest.mark.parametrize(
    ("request_", "found"),
    [
        (
            {
                "method": "GET",
                "url": "https://p.invalid/a",
                "headers": [["X-Api-Key", "k-1234567"]],
            },
            "header X-Api-Key",
        ),
        (
            {
                "method": "GET",
                "url": "https://p.invalid/a?api_key=k-1234567",
                "headers": [],
            },
            "parameter api_key",
        ),
        (
            {
                "method": "POST",
                "url": "https://p.invalid/a",
                "headers": [],
                "body": {"json": {"auth": {"password": "k-1234567"}}},
            },
            "field password",
        ),
        (
            {"method": "GET", "url": f"https://p.invalid/a/{SECRET}", "headers": []},
            "a known secret",
        ),
    ],
    ids=["header", "parameter", "body field", "known value"],
)
def test_the_lint_finds_a_secret_left_on_a_tape(
    tmp_path: Path, request_: dict, found: str
) -> None:
    """It names each place of a tape holding what looks like a secret.

    Scenario Outline: The lint finds a secret left on a tape
      Given a tape file holding a call whose request carries a secret in its <place>
      When the tape is linted, knowing the key
      Then the lint names calls[0] and the <place>
    """
    path = tmp_path / "tape.json"
    _given_tape_holding(
        path,
        sdk.TapedHttpCall(
            request=sdk.TapedHttpRequest.model_validate(request_),
            response=sdk.TapedHttpResponse(status=200),
        ),
    )
    findings = _given_lint()(str(path), secrets=[SECRET])
    assert any("calls[0]" in f and found in f for f in findings), findings
