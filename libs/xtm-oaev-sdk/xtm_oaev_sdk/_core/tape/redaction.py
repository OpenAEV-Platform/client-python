"""Keeps secrets off the tape, the same way when recording and when replaying, so a
replayed call matches its recording whatever secret it carries."""

import re
from typing import Iterable, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

__all__ = ["Redaction"]

MASK = "***"
_MIN_SECRET_LENGTH = 4
#: Header and parameter names that carry a secret, whatever their value.
_SECRET_NAME = re.compile(
    r"(^|[-_])(key|token|secret|password|passwd|apikey|auth|authorization"
    r"|cookie|credentials?|signature)$|api[-_]?key|access[-_]?token",
    re.IGNORECASE,
)
_FORM_FIELD = re.compile(
    r"(?i)((?:^|[&?])[\w.-]*(?:key|token|secret|password|passwd)=)[^&\s]*"
)
_JSON_FIELD = re.compile(
    r'(?i)("[\w.-]*(?:key|token|secret|password|passwd)"\s*:\s*")[^"]*(")'
)


class Redaction:
    """Masks the known secret values, and the values of secret-named fields."""

    def __init__(self, secrets: Iterable[str]) -> None:
        self._secrets = sorted(
            {s for s in secrets if s and len(s) >= _MIN_SECRET_LENGTH},
            key=len,
            reverse=True,
        )

    @staticmethod
    def secret_name(name: str) -> bool:
        return bool(_SECRET_NAME.search(name.strip()))

    def text(self, value: str) -> str:
        for secret in self._secrets:
            value = value.replace(secret, MASK)
        return value

    def body(self, value: str) -> str:
        value = _FORM_FIELD.sub(lambda m: m.group(1) + MASK, self.text(value))
        return _JSON_FIELD.sub(lambda m: m.group(1) + MASK + m.group(2), value)

    def url(self, url: str) -> str:
        parts = urlsplit(url)
        query = [
            (name, MASK if self.secret_name(name) else self.text(value))
            for name, value in parse_qsl(parts.query, keep_blank_values=True)
        ]
        return self.text(
            urlunsplit(
                parts._replace(
                    path=self.text(parts.path), query=urlencode(query, safe="*")
                )
            )
        )

    def headers(self, headers: Sequence[tuple[str, str]]) -> list[tuple[str, str]]:
        return [
            (name, MASK if self.secret_name(name) else self.text(value))
            for name, value in headers
        ]

    def argv(self, argv: Sequence[str]) -> list[str]:
        return [self.text(arg) for arg in argv]
