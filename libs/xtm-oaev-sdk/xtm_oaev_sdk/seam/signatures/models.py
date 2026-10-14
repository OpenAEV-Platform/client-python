"""Signature data contracts: matching vocabulary, matching policies and the
extra signatures merged into the default ones.

The inbound I/O models live in :mod:`xtm_oaev_sdk.seam.signatures.seam` and the
wire models in :mod:`xtm_oaev_sdk.seam.port_io`.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, JsonValue
from xtm_oaev_sdk.seam.common import OpenAEVError

__all__ = [
    "ExtraSignatureData",
    "MatchTypes",
    "SignatureMatch",
    "SignatureType",
    "SignatureTypes",
]


class MatchTypes(str, Enum):
    """Supported match algorithm types for signature evaluation."""

    MATCH_TYPE_FUZZY = "fuzzy"
    MATCH_TYPE_SIMPLE = "simple"


class SignatureTypes(str, Enum):
    """Supported signature field identifiers."""

    SIG_TYPE_PROCESS_NAME = "process_name"
    SIG_TYPE_PARENT_PROCESS_NAME = "parent_process_name"
    SIG_TYPE_COMMAND_LINE = "command_line"
    SIG_TYPE_IPV4_ADDRESS = "ipv4_address"
    SIG_TYPE_IPV6_ADDRESS = "ipv6_address"
    SIG_TYPE_SOURCE_IPV4_ADDRESS = "source_ipv4_address"
    SIG_TYPE_SOURCE_IPV6_ADDRESS = "source_ipv6_address"
    SIG_TYPE_TARGET_IPV4_ADDRESS = "target_ipv4_address"
    SIG_TYPE_TARGET_IPV6_ADDRESS = "target_ipv6_address"
    SIG_TYPE_HOSTNAME = "hostname"
    SIG_TYPE_TARGET_HOSTNAME_ADDRESS = "target_hostname_address"
    SIG_TYPE_START_DATE = "start_date"
    SIG_TYPE_END_DATE = "end_date"
    SIG_TYPE_CLOUD_PROVIDER = "cloud_provider"
    SIG_TYPE_CLOUD_ACCOUNT_ID = "cloud_account_id"
    SIG_TYPE_CLOUD_REGION = "cloud_region"
    SIG_TYPE_TARGET_SERVICE = "target_service"
    SIG_TYPE_QUERY = "query"
    SIG_TYPE_URL_HASH = "url_hash"
    SIG_TYPE_FILE_NAME = "file_name"
    SIG_TYPE_FILE_HASH = "file_hash"
    SIG_TYPE_SOURCE_EMAIL = "source_email"
    SIG_TYPE_TARGET_EMAIL = "target_email"
    SIG_TYPE_EMAIL_CUSTOM_HEADER = "email_custom_header"
    # AI adversarial validation: correlate AI defense (LLM firewall / guardrail) events back to a
    # specific AI inject execution.
    SIG_TYPE_AI_REQUEST_MARKER = "ai_request_marker"
    SIG_TYPE_AI_TARGET_ENDPOINT = "ai_target_endpoint"


class SignatureMatch:
    """Represents a signature matching outcome.

    Args:
        match_type: The matching strategy/result type.
        match_score: Optional score produced by matching.

    Raises:
        OpenAEVError: If `match_score` is not provided for non-simple match
            types.
    """

    def __init__(self, match_type: MatchTypes, match_score: int | None):
        if match_score is None and match_type != MatchTypes.MATCH_TYPE_SIMPLE:
            raise OpenAEVError(
                f"Match type {match_type} requires score to be set, found score = {match_score}"
            )
        self.match_type = match_type
        self.match_score = match_score


class SignatureType:
    """Describe a signature type and its matching policy.

    Args:
        label: Type specifier.
        match_type: Matching policy used when trying to match this signature
            type, for example fuzzy or simple.
        match_score: Threshold score used when ``match_type`` is fuzzy.
    """

    def __init__(
        self,
        label: SignatureTypes,
        match_type: MatchTypes = MatchTypes.MATCH_TYPE_SIMPLE,
        match_score: int | None = None,
    ) -> None:
        self.label = label
        self.match_policy = SignatureMatch(match_type, match_score)

    def make_struct_for_matching(self, data: Any) -> dict[str, Any]:
        """Format matching metadata for helper-based signature matching.

        Args:
            data: Arbitrary data, most often a string or numeric primitive.

        Returns:
            A dictionary with matching specifiers containing:
                - ``type``: Matching type string.
                - ``data``: Provided data payload.
                - ``score``: Optional score threshold when configured.
        """
        struct: dict[str, Any] = {
            "type": self.match_policy.match_type.value,
            "data": data,
        }

        if self.match_policy.match_score is not None:
            struct["score"] = self.match_policy.match_score

        return struct


class ExtraSignatureData(BaseModel):
    """Format for extra signatures added to the default signatures."""

    detection: dict[str, JsonValue] = Field(default_factory=dict)
    prevention: dict[str, JsonValue] = Field(default_factory=dict)
    vulnerability: dict[str, JsonValue] = Field(default_factory=dict)

    def get_extra(self, expectation_type: str) -> dict[str, JsonValue]:
        if expectation_type.lower() == "detection":
            return self.detection
        if expectation_type.lower() == "prevention":
            return self.prevention
        if expectation_type.lower() == "vulnerability":
            return self.vulnerability
        raise ValueError(
            f"Expectation type should be one of the available parameters: {list(self.model_fields.keys())}"
        )
