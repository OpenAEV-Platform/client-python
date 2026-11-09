"""Call tape data contracts: the tape document and the outside calls it holds.

A tape is one JSON document, meant to be read, committed and reviewed in a diff: a
header (``tape_version``, ``sdk_version``, ``daemon``, ``recorded_at``), then the calls,
in the order made. A body is kept as JSON when it is a JSON object or list, as text when
it is UTF-8, else in base64.
"""

import base64
import json
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from xtm_oaev_sdk.seam.common import OpenAEVError

__all__ = [
    "TAPE_VERSION",
    "Tape",
    "TapeMissError",
    "TapedBody",
    "TapedCall",
    "TapedCommand",
    "TapedHttpCall",
    "TapedHttpRequest",
    "TapedHttpResponse",
]

#: Version of the tape document. A tape of another version is refused on replay.
TAPE_VERSION = "1"


class TapeMissError(OpenAEVError, ConnectionError):
    """A call the replay tape does not hold. It is a ``ConnectionError``, so HTTP
    clients report it as the connection failure it stands for."""


class TapedBody(BaseModel):
    """Bytes on the tape: as JSON (``json``) when they are a JSON object or list, as
    text (``text``) when they are UTF-8, else in base64 (``base64``)."""

    model_config = ConfigDict(
        extra="forbid", populate_by_name=True, serialize_by_alias=True
    )

    json_value: JsonValue = Field(default=None, alias="json")
    text: str | None = None
    base64: str | None = None

    @model_validator(mode="after")
    def holds_one_form(self) -> "TapedBody":
        forms = {"json_value", "text", "base64"} & self.model_fields_set
        if len(forms) > 1:
            raise ValueError("a taped body is json, text or base64, not several")
        return self

    @classmethod
    def of(cls, data: bytes | str | None) -> "TapedBody | None":
        if data is None:
            return None
        if isinstance(data, bytes):
            try:
                data = data.decode("utf-8")
            except UnicodeDecodeError:
                return cls(base64=base64.b64encode(data).decode("ascii"))
        try:
            document = json.loads(data)
        except ValueError:
            document = None
        if isinstance(document, (dict, list)):
            return cls(json_value=document)
        return cls(text=data)

    def as_text(self) -> str:
        if "json_value" in self.model_fields_set:
            return json.dumps(self.json_value)
        if self.base64 is not None:
            return base64.b64decode(self.base64).decode("utf-8", errors="replace")
        return self.text or ""

    def as_bytes(self) -> bytes:
        if self.base64 is not None:
            return base64.b64decode(self.base64)
        return self.as_text().encode("utf-8")

    def match_key(self) -> str:
        """What replay compares: JSON by value, whatever its spacing or key order."""
        if "json_value" in self.model_fields_set:
            return json.dumps(self.json_value, sort_keys=True, separators=(",", ":"))
        return self.as_text()


class TapedHttpRequest(BaseModel):
    """An HTTP request, as sent: method, absolute URL, headers, body."""

    model_config = ConfigDict(extra="forbid")

    method: str
    url: str
    headers: list[tuple[str, str]] = Field(default_factory=list)
    body: TapedBody | None = None


class TapedHttpResponse(BaseModel):
    """An HTTP response, as received: status, reason, headers, body. A compressed body
    is kept decompressed when it is readable, ``decoded_from`` naming its encoding, and
    replays without its ``Content-Encoding``."""

    model_config = ConfigDict(extra="forbid")

    status: int
    reason: str = ""
    headers: list[tuple[str, str]] = Field(default_factory=list)
    body: TapedBody | None = None
    decoded_from: str | None = None


class TapedHttpCall(BaseModel):
    """One HTTP call and its answer."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["http"] = "http"
    request: TapedHttpRequest
    response: TapedHttpResponse


class TapedCommand(BaseModel):
    """One command run through ``subprocess.run``, and its result. ``error`` holds the
    error that stopped it from starting (the command not found), if any."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["command"] = "command"
    argv: list[str]
    input: TapedBody | None = None
    returncode: int = 0
    stdout: TapedBody | None = None
    stderr: TapedBody | None = None
    error: str | None = None


#: One call of a tape.
TapedCall = Annotated[Union[TapedHttpCall, TapedCommand], Field(discriminator="kind")]


class Tape(BaseModel):
    """A tape: its header, then the calls in the order made."""

    model_config = ConfigDict(extra="forbid")

    tape_version: str = TAPE_VERSION
    sdk_version: str
    daemon: str | None = None
    recorded_at: str
    calls: list[TapedCall] = Field(default_factory=list)

    def document(self) -> dict[str, Any]:
        """The tape as the JSON document written to its file."""
        return self.model_dump(mode="json", exclude_none=True)
