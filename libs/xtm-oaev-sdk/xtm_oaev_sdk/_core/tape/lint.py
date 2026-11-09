"""Tape lint: finds what looks like a secret left on a tape, before it is committed.

It names each place holding a known secret value, and each secret-named header, query
parameter or JSON field (``Authorization``, ``api_key``, ``password``…) whose value is
not masked. A tape recorded with its secrets redacted lints clean.
"""

import json
from typing import Any, Iterator, Sequence
from urllib.parse import parse_qsl, urlsplit

from .redaction import MASK, Redaction

__all__ = ["lint_tape"]

_MIN_SECRET_LENGTH = 4


def _unmasked(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value != MASK


def _fields(document: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(document, dict):
        for key, value in document.items():
            yield str(key), value
            yield from _fields(value)
    elif isinstance(document, list):
        for item in document:
            yield from _fields(item)


def _http_findings(where: str, message: dict[str, Any]) -> Iterator[str]:
    for name, value in message.get("headers") or []:
        if Redaction.secret_name(str(name)) and _unmasked(value):
            yield f"{where} header {name} holds a value that is not masked"
    url = message.get("url")
    if isinstance(url, str):
        for name, value in parse_qsl(urlsplit(url).query, keep_blank_values=True):
            if Redaction.secret_name(name) and _unmasked(value):
                yield f"{where} parameter {name} holds a value that is not masked"
    body = message.get("body") or {}
    for name, value in _fields(body.get("json") if isinstance(body, dict) else None):
        if Redaction.secret_name(name) and _unmasked(value):
            yield f"{where} field {name} holds a value that is not masked"


def lint_tape(path: str, secrets: Sequence[str]) -> list[str]:
    """Each place of the tape at ``path`` holding what looks like a secret."""
    with open(path, encoding="utf-8") as handle:
        document = json.load(handle)
    known = [s for s in secrets if s and len(s) >= _MIN_SECRET_LENGTH]
    calls = document.get("calls") if isinstance(document, dict) else None
    findings: list[str] = []
    for number, call in enumerate(calls if isinstance(calls, list) else []):
        where = f"calls[{number}]"
        text = json.dumps(call, ensure_ascii=False)
        if any(secret in text or json.dumps(secret)[1:-1] in text for secret in known):
            findings.append(f"{where} holds a known secret")
        if isinstance(call, dict) and call.get("kind") == "http":
            for side in ("request", "response"):
                message = call.get(side)
                if isinstance(message, dict):
                    findings.extend(_http_findings(f"{where} {side}", message))
    return findings
