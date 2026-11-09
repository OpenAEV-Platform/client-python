"""Dev sink: writes the calls a daemon in dev mode would have sent to the platform.

Each call is checked against the payload the platform accepts on its path, redacted,
and kept in one JSON list: rewritten whole after each call when it goes to a file, so the
file is valid JSON at any time, or written once, on close, to stdout or stderr.
"""

import json
import os
import re
import sys
import tempfile
import threading
from typing import Any, Iterable, Mapping, Sequence

from pydantic import ValidationError
from xtm_oaev_sdk.seam.common import OpenAEVHttpError
from xtm_oaev_sdk.seam.port_io import (
    InjectExecutionInput,
    InjectExpectationBulkUpdateInput,
    InjectExpectationTraceBulkInsertInput,
    InjectExpectationUpdateFromCollectorInput,
    InjectReceptionInput,
)

__all__ = ["DevSink", "DevSinkFactory"]

MASK = "***"
#: Shorter values would redact ordinary words.
_MIN_SECRET_LENGTH = 4
_SECRET_VARIABLE = re.compile(r"(TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|_KEY)$", re.I)
#: What the platform accepts on each path a daemon calls.
_PAYLOADS = (
    (
        "POST",
        re.compile(r"^/api/injects/execution/reception/[^/]+$"),
        InjectReceptionInput,
    ),
    (
        "POST",
        re.compile(r"^/api/injects/execution/callback/[^/]+$"),
        InjectExecutionInput,
    ),
    (
        "PUT",
        re.compile(r"^/api/injects/expectations/bulk$"),
        InjectExpectationBulkUpdateInput,
    ),
    (
        "PUT",
        re.compile(r"^/api/injects/expectations/[^/]+$"),
        InjectExpectationUpdateFromCollectorInput,
    ),
    (
        "POST",
        re.compile(r"^/api/inject-expectations-traces/bulk$"),
        InjectExpectationTraceBulkInsertInput,
    ),
)


def _checked(method: str, path: str, body: Any) -> Any:
    """``body`` as the platform would take it, in its payload's field order; refused
    with a 400 when the platform would reject it."""
    model = next(
        (
            model
            for verb, pattern, model in _PAYLOADS
            if verb == method.upper() and pattern.match(path)
        ),
        None,
    )
    if model is None:
        return body
    try:
        payload = model.model_validate(body)
    except ValidationError as error:
        raise OpenAEVHttpError(
            error_message=f"the platform would reject {method} {path}: {error}",
            response_code=400,
        ) from error
    return payload.model_dump(mode="json", exclude_unset=True)


class DevSink:
    """Implements ``DevSinkPort``."""

    def __init__(
        self,
        out: str | None,
        secrets: Sequence[str],
        keep: Iterable[str],
        to_stderr: bool,
    ) -> None:
        self._out = out
        self._to_stderr = to_stderr
        self._secrets = sorted(
            {s for s in secrets if s and len(s) >= _MIN_SECRET_LENGTH},
            key=len,
            reverse=True,
        )
        self._keep = frozenset(keep)
        self._changed = threading.Condition()
        self._written: list[dict[str, Any]] = []
        self._closed = False
        self.calls: list[dict[str, Any]] = []
        if out:
            self._write_file()

    def _text(self) -> str:
        return json.dumps(self._written, indent=2, ensure_ascii=False) + "\n"

    def _write_file(self) -> None:
        directory = os.path.dirname(os.path.abspath(self._out))
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=directory, delete=False, suffix=".tmp"
        ) as handle:
            handle.write(self._text())
        os.replace(handle.name, self._out)

    def _holds_secret(self, text: str) -> bool:
        return any(
            secret in text or json.dumps(secret)[1:-1] in text
            for secret in self._secrets
        )

    def redact(self, value: Any, key: str | None = None) -> Any:
        if key in self._keep:
            return value
        if isinstance(value, dict):
            return {k: self.redact(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        if not isinstance(value, str) or not self._holds_secret(value):
            return value
        try:
            document = json.loads(value)
        except ValueError:
            document = None
        if isinstance(document, (dict, list)):
            return json.dumps(self.redact(document))
        for secret in self._secrets:
            value = value.replace(secret, MASK)
        return value

    def record(self, method: str, path: str, body: Any) -> None:
        checked = _checked(method, path, body)
        with self._changed:
            self.calls.append({"method": method, "path": path, "body": body})
            self._written.append(
                {"method": method, "path": path, "body": self.redact(checked)}
            )
            if self._out:
                self._write_file()
            self._changed.notify_all()

    def note(self, text: str) -> None:
        sys.stderr.write(f"dev: {self.redact(text)}\n")
        sys.stderr.flush()

    def refuse(self, reason: str) -> int:
        self.note(f"refused: {reason}")
        return 2

    def close(self) -> None:
        with self._changed:
            if self._closed:
                return
            self._closed = True
            if self._out:
                self._write_file()
                return
            stream = sys.stderr if self._to_stderr else sys.stdout
            stream.write(self._text())
            stream.flush()


class DevSinkFactory:
    """Implements ``DevSinkFactoryPort``."""

    def open(
        self,
        out: str | None,
        secrets: Sequence[str],
        keep: Iterable[str],
        to_stderr: bool,
    ) -> DevSink:
        return DevSink(out, secrets, keep, to_stderr)

    def environment_secrets(self, environ: Mapping[str, str] | None) -> list[str]:
        environ = os.environ if environ is None else environ
        return [
            value
            for name, value in environ.items()
            if _SECRET_VARIABLE.search(name) and len(value) >= _MIN_SECRET_LENGTH
        ]
