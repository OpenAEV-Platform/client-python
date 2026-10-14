"""Enumerations used by the signature engine.

The wire vocabulary — the three enums that appear in the port I/O JSON
schema (``SignatureExpectationType``, ``ExecutionStatus``,
``InjectExecutionActions``) — is owned by the seam
(``xtm_oaev_sdk.seam.port_io.models``) and re-exported here so internal
import paths stay stable. The matching-engine vocabulary (``MatchTypes``,
``SignatureTypes``) never crosses the wire and stays defined here.
"""

from enum import Enum

from xtm_oaev_sdk.seam.port_io.models import (
    ExecutionStatus,
    InjectExecutionActions,
    SignatureExpectationType,
)

__all__ = [
    "SignatureExpectationType",
    "ExecutionStatus",
    "InjectExecutionActions",
    "MatchTypes",
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
