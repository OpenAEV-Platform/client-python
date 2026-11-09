"""Call tape engine: hooks the process's outside calls to record or replay them.

HTTP is hooked at ``http.client``, which ``urllib.request``, urllib3 and so
``requests`` all go through: the request is read as it is built, the answer at
``getresponse``. The tape is one JSON document (``Tape``), rewritten whole after each
call, so the file is valid JSON at any time; a JSON body is kept as JSON, and a
compressed answer decompressed when readable. On replay no socket ever opens: each
connection gets a local
socketpair instead (urllib3's own ``connect`` included, when urllib3 is loaded), and
``getresponse`` answers from the tape. Commands are hooked at ``subprocess.run``.
"""

import base64
import gzip
import http.client
import importlib
import importlib.metadata
import io
import json
import os
import socket
import subprocess
import tempfile
import threading
import zlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from pydantic import TypeAdapter, ValidationError
from xtm_oaev_sdk.seam.common import OpenAEVError
from xtm_oaev_sdk.seam.tape import (
    TAPE_VERSION,
    Tape,
    TapedBody,
    TapedCall,
    TapedCommand,
    TapedHttpCall,
    TapedHttpRequest,
    TapedHttpResponse,
    TapeMissError,
)

from .lint import lint_tape
from .redaction import Redaction

__all__ = ["CallTapeEngine"]

#: Marks a patched method that was inherited, removed again on stop.
_INHERITED = object()


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


_MODES = ("record", "replay")
_CALL = TypeAdapter(TapedCall)
#: Encodings a taped answer is decompressed from, when the result is readable.
_DECODERS = {
    "gzip": gzip.decompress,
    "x-gzip": gzip.decompress,
    "deflate": zlib.decompress,
}
_NO_BODY_STATUSES = (204, 304)


class _BytesSocket:
    """What ``http.client.HTTPResponse`` reads a response from."""

    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def makefile(self, *_: Any, **__: Any) -> io.BytesIO:
        return io.BytesIO(self._raw)


def _response(answer: TapedHttpResponse, method: str) -> http.client.HTTPResponse:
    body = answer.body.as_bytes() if answer.body else b""
    lines = [f"HTTP/1.1 {answer.status} {answer.reason}"]
    lines += [
        f"{name}: {value}"
        for name, value in answer.headers
        if name.lower() not in ("transfer-encoding", "content-length")
    ]
    if method != "HEAD" and answer.status not in _NO_BODY_STATUSES:
        lines.append(f"Content-Length: {len(body)}")
    raw = ("\r\n".join(lines) + "\r\n\r\n").encode("latin-1", errors="replace")
    response = http.client.HTTPResponse(_BytesSocket(raw + body), method=method)
    response.begin()
    return response


def _bytes(data: Any) -> bytes | None:
    if data is None:
        return None
    if isinstance(data, str):
        return data.encode("utf-8")
    if isinstance(data, (bytes, bytearray, memoryview)):
        return bytes(data)
    if hasattr(data, "read"):
        return None
    try:
        return b"".join(bytes(chunk) for chunk in data)
    except TypeError:
        return None


def _scheme(connection: Any) -> str:
    return "https" if getattr(connection, "default_port", 80) == 443 else "http"


def _url(connection: Any, target: str) -> str:
    if target.startswith(("http://", "https://")):
        return target
    host = str(connection.host)
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    port = connection.port or connection.default_port
    netloc = host if port == connection.default_port else f"{host}:{port}"
    return f"{_scheme(connection)}://{netloc}{target}"


def _sdk_version() -> str:
    try:
        return importlib.metadata.version("xtm-oaev-sdk")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _address(address: Any) -> str:
    if isinstance(address, tuple) and len(address) >= 2:
        return f"{address[0]}:{address[1]}"
    return str(address)


def _decoded(body: bytes, headers: list[tuple[str, str]]) -> tuple[bytes, str | None]:
    """The answer's body decompressed, and the encoding it came in, when readable."""
    encoding = next(
        (v.strip().lower() for n, v in headers if n.lower() == "content-encoding"), ""
    )
    decoder = _DECODERS.get(encoding)
    if decoder is None:
        return body, None
    try:
        decoded = decoder(body)
        decoded.decode("utf-8")
    except (OSError, EOFError, zlib.error, UnicodeDecodeError):
        return body, None
    return decoded, encoding


class CallTapeEngine:
    """Implements ``CallTapePort``."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._mode: str | None = None
        self._redaction = Redaction(())
        self._path: str | None = None
        self._tape: Tape | None = None
        self._answers: dict[tuple, list[Any]] = defaultdict(list)
        self._served: dict[tuple, int] = defaultdict(int)
        self._peers: list[socket.socket] = []
        self._patched: list[tuple[Any, str, Any]] = []

    # -- port --------------------------------------------------------------------

    def check(self, path: str, mode: str) -> None:
        if mode not in _MODES:
            raise ValueError(f"a call tape records or replays, not {mode!r}")

    def start(
        self, path: str, mode: str, secrets: Sequence[str], daemon: str | None
    ) -> None:
        self.check(path, mode)
        with self._lock:
            if self._mode is not None:
                raise OpenAEVError("a call tape already runs in this process")
            self._redaction = Redaction(secrets)
            self._answers.clear()
            self._served.clear()
            if mode == "record":
                self._path = path
                self._tape = Tape(
                    sdk_version=_sdk_version(),
                    daemon=daemon,
                    recorded_at=datetime.now(timezone.utc)
                    .isoformat(timespec="seconds")
                    .replace("+00:00", "Z"),
                )
                self._save()
            else:
                self._load(path)
            self._mode = mode
            self._install()

    def stop(self) -> None:
        with self._lock:
            if self._mode is None:
                return
            for owner, name, original in reversed(self._patched):
                if original is _INHERITED:
                    delattr(owner, name)
                else:
                    setattr(owner, name, original)
            self._patched.clear()
            for peer in self._peers:
                peer.close()
            self._peers.clear()
            self._path = None
            self._tape = None
            self._mode = None

    def lint(self, path: str, secrets: Sequence[str]) -> list[str]:
        return lint_tape(path, secrets)

    # -- tape --------------------------------------------------------------------

    def _load(self, path: str) -> None:
        try:
            with open(path, encoding="utf-8") as handle:
                document = json.load(handle)
        except ValueError as error:
            raise OpenAEVError(f"{path} is not a JSON tape: {error}") from error
        if not isinstance(document, dict):
            raise OpenAEVError(f"{path} is not a JSON tape: it is no JSON object")
        version = document.get("tape_version")
        if version != TAPE_VERSION:
            raise OpenAEVError(
                f"{path}: unsupported tape version {version!r}, this SDK replays"
                f" version {TAPE_VERSION!r}"
            )
        calls = document.get("calls")
        for number, raw in enumerate(calls if isinstance(calls, list) else []):
            try:
                call = _CALL.validate_python(raw)
            except ValidationError as error:
                raise OpenAEVError(
                    f"{path}: calls[{number}] is not a taped call: {error}"
                ) from error
            if isinstance(call, TapedHttpCall):
                key = self._http_key(call.request)
                self._answers[key].append(call.response)
            else:
                self._answers[self._command_key(call.argv, call.input)].append(call)

    def _save(self) -> None:
        """Rewrite the tape whole, through a temporary file, so it is valid JSON at
        any time."""
        text = json.dumps(self._tape.document(), indent=2, ensure_ascii=False) + "\n"
        directory = os.path.dirname(os.path.abspath(self._path))
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
        ) as handle:
            handle.write(text)
        os.replace(handle.name, self._path)

    def _write(self, call: Any) -> None:
        with self._lock:
            if self._tape is not None:
                self._tape.calls.append(call)
                self._save()

    def _take(self, key: tuple) -> Any:
        with self._lock:
            answers = self._answers.get(key)
            if not answers:
                return None
            index = min(self._served[key], len(answers) - 1)
            self._served[key] += 1
            return answers[index]

    def _http_key(self, request: TapedHttpRequest) -> tuple:
        body = self._redacted_body(request.body)
        return (
            "http",
            request.method.upper(),
            self._redaction.url(request.url),
            body.match_key() if body is not None else "",
        )

    def _redacted_body(self, body: TapedBody | None) -> TapedBody | None:
        """``body`` with its secrets and secret-named fields masked, kept as JSON when
        it is JSON."""
        if body is None or body.base64 is not None:
            return body
        return TapedBody.of(self._redaction.body(body.as_text()))

    def _command_key(self, argv: Sequence[str], given: TapedBody | None) -> tuple:
        text = given.as_text() if given else ""
        return (
            "command",
            json.dumps(self._redaction.argv(argv)),
            self._redaction.text(text),
        )

    def _redacted_request(self, state: dict[str, Any]) -> TapedHttpRequest:
        body = bytes(state["body"]) if state["body"] else None
        taped = self._redacted_body(TapedBody.of(body))
        return TapedHttpRequest(
            method=state["method"],
            url=self._redaction.url(state["url"]),
            headers=self._redaction.headers(state["headers"]),
            body=taped,
        )

    # -- hooks -------------------------------------------------------------------

    def _patch(self, owner: Any, name: str, make: Callable[[Any], Any]) -> None:
        original = owner.__dict__.get(name)
        if original is None:
            return
        self._patched.append((owner, name, original))
        setattr(owner, name, make(original))

    def _patch_inherited(
        self, owner: Any, name: str, make: Callable[[Any], Any]
    ) -> None:
        """Patch a method ``owner`` inherits from a C base, removed again on stop."""
        self._patched.append((owner, name, owner.__dict__.get(name, _INHERITED)))
        setattr(owner, name, make(getattr(owner, name)))

    def _install(self) -> None:
        connection = http.client.HTTPConnection
        self._patch(connection, "putrequest", self._putrequest)
        self._patch(connection, "putheader", self._putheader)
        self._patch(connection, "endheaders", self._endheaders)
        self._patch(connection, "send", self._send)
        self._patch(connection, "getresponse", self._getresponse)
        self._patch(subprocess, "run", self._run)
        if self._mode == "replay":
            owners = [http.client.HTTPConnection, http.client.HTTPSConnection]
            try:
                urllib3_connection = importlib.import_module("urllib3.connection")
                owners += [
                    urllib3_connection.HTTPConnection,
                    urllib3_connection.HTTPSConnection,
                ]
            except ImportError:
                pass
            for owner in owners:
                self._patch(owner, "connect", self._connect)
            # Fail closed: any other outbound connection is a call off the tape.
            self._patch_inherited(socket.socket, "connect", self._closed_connect)
            self._patch_inherited(socket.socket, "connect_ex", self._closed_connect)

    def _putrequest(self, original: Callable) -> Callable:
        def putrequest(conn: Any, method: str, url: str, *args: Any, **kwargs: Any):
            conn._tape_request = {
                "method": method,
                "url": _url(conn, url),
                "headers": [],
                "body": bytearray(),
                "sent": False,
            }
            return original(conn, method, url, *args, **kwargs)

        return putrequest

    def _putheader(self, original: Callable) -> Callable:
        def putheader(conn: Any, header: Any, *values: Any) -> Any:
            state = getattr(conn, "_tape_request", None)
            if state is not None:
                name = header.decode("latin-1") if isinstance(header, bytes) else header
                value = ", ".join(
                    v.decode("latin-1") if isinstance(v, bytes) else str(v)
                    for v in values
                )
                state["headers"].append((str(name), value))
            return original(conn, header, *values)

        return putheader

    def _endheaders(self, original: Callable) -> Callable:
        def endheaders(conn: Any, message_body: Any = None, **kwargs: Any) -> Any:
            state = getattr(conn, "_tape_request", None)
            if state is not None:
                data = _bytes(message_body)
                if data:
                    state["body"] += data
            result = original(conn, message_body, **kwargs)
            if state is not None:
                state["sent"] = True
            return result

        return endheaders

    def _send(self, original: Callable) -> Callable:
        engine = self

        def send(conn: Any, data: Any) -> Any:
            state = getattr(conn, "_tape_request", None)
            if state is not None and state["sent"]:
                chunk = _bytes(data)
                if chunk:
                    state["body"] += chunk
            if engine._mode == "replay":
                # Nothing is sent, but the connection gets its (local) socket as if it
                # had been: urllib3 sets its timeout before reading the answer.
                if getattr(conn, "sock", None) is None:
                    conn.connect()
                return None
            return original(conn, data)

        return send

    def _getresponse(self, original: Callable) -> Callable:
        engine = self

        def getresponse(conn: Any) -> Any:
            state = getattr(conn, "_tape_request", None)
            if state is None:
                return original(conn)
            conn._tape_request = None
            request = engine._redacted_request(state)
            if engine._mode == "record":
                real = original(conn)
                body = real.read()
                headers = list(real.msg.items())
                taped_body, decoded_from = _decoded(body, headers)
                taped_headers = headers
                if decoded_from is not None:
                    taped_headers = [
                        (n, v)
                        for n, v in headers
                        if n.lower() not in ("content-encoding", "content-length")
                    ]
                answer = TapedHttpResponse(
                    status=real.status,
                    reason=real.reason or "",
                    headers=engine._redaction.headers(taped_headers),
                    body=engine._taped_output(taped_body),
                    decoded_from=decoded_from,
                )
                engine._write(TapedHttpCall(request=request, response=answer))
                # The daemon gets the answer as the API sent it.
                original_answer = TapedHttpResponse(
                    status=real.status,
                    reason=real.reason or "",
                    headers=headers,
                    body=TapedBody(base64=_b64(body)) if body else None,
                )
                return _response(original_answer, state["method"])
            answer = engine._take(engine._http_key(request))
            conn._HTTPConnection__state = http.client._CS_IDLE
            conn._HTTPConnection__response = None
            if answer is None:
                raise TapeMissError(
                    f"not on the replay tape: {request.method} {request.url}"
                )
            return _response(answer, state["method"])

        return getresponse

    def _closed_connect(self, original: Callable) -> Callable:
        def connect(sock: Any, address: Any, *args: Any, **kwargs: Any) -> Any:
            if sock.family in (socket.AF_INET, socket.AF_INET6):
                raise TapeMissError(
                    f"not on the replay tape: connection to {_address(address)}"
                )
            return original(sock, address, *args, **kwargs)

        return connect

    def _connect(self, original: Callable) -> Callable:
        engine = self

        def connect(conn: Any) -> None:
            local, peer = socket.socketpair()
            engine._peers.append(peer)
            conn.sock = local
            for name, value in (
                ("is_verified", True),
                ("proxy_is_verified", None),
                ("_has_connected_to_proxy", False),
            ):
                try:
                    setattr(conn, name, value)
                except AttributeError:
                    pass

        return connect

    def _run(self, original: Callable) -> Callable:
        engine = self

        def run(*popenargs: Any, **kwargs: Any) -> Any:
            args = popenargs[0] if popenargs else kwargs.get("args")
            if isinstance(args, (str, bytes)):
                argv = [args.decode() if isinstance(args, bytes) else args]
            else:
                argv = [a.decode() if isinstance(a, bytes) else str(a) for a in args]
            given = TapedBody.of(kwargs.get("input"))
            if engine._mode == "record":
                return engine._record_command(original, argv, given, popenargs, kwargs)
            return engine._replay_command(args, argv, given, kwargs)

        return run

    def _taped_output(self, data: Any) -> TapedBody | None:
        taped = TapedBody.of(data)
        if taped is None or taped.base64 is not None:
            return taped
        return TapedBody.of(self._redaction.text(taped.as_text()))

    def _record_command(
        self,
        original: Callable,
        argv: list[str],
        given: TapedBody | None,
        popenargs: tuple,
        kwargs: dict,
    ) -> Any:
        taped = TapedCommand(argv=self._redaction.argv(argv), input=given)
        try:
            result = original(*popenargs, **kwargs)
        except subprocess.CalledProcessError as failure:
            self._write(
                taped.model_copy(
                    update={
                        "returncode": failure.returncode,
                        "stdout": self._taped_output(failure.output),
                        "stderr": self._taped_output(failure.stderr),
                    }
                )
            )
            raise
        except FileNotFoundError as failure:
            self._write(taped.model_copy(update={"error": str(failure)}))
            raise
        self._write(
            taped.model_copy(
                update={
                    "returncode": result.returncode,
                    "stdout": self._taped_output(result.stdout),
                    "stderr": self._taped_output(result.stderr),
                }
            )
        )
        return result

    def _replay_command(
        self, args: Any, argv: list[str], given: TapedBody | None, kwargs: dict
    ) -> Any:
        taped = self._take(self._command_key(argv, given))
        if taped is None:
            raise TapeMissError(f"not on the replay tape: command {argv}")
        if taped.error is not None:
            raise FileNotFoundError(taped.error)
        as_text = any(
            kwargs.get(name) for name in ("text", "universal_newlines", "encoding")
        )

        def output(body: TapedBody | None) -> Any:
            if body is None:
                return None
            return body.as_text() if as_text else body.as_bytes()

        stdout, stderr = output(taped.stdout), output(taped.stderr)
        if kwargs.get("check") and taped.returncode:
            raise subprocess.CalledProcessError(taped.returncode, args, stdout, stderr)
        return subprocess.CompletedProcess(args, taped.returncode, stdout, stderr)
