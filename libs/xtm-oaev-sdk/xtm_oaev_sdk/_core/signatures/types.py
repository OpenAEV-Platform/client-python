"""Enumerations used by signature engine types.

This module defines shared enum constants for signature expectations,
execution actions, match behavior, and signature field types.
"""

from enum import Enum

__all__ = [
    "SignatureExpectationType",
    "InjectExecutionActions",
    "MatchTypes",
    "SignatureTypes",
]


class SignatureExpectationType(str, Enum):
    """Expectation categories for a signature."""

    DETECTION = "DETECTION"
    PREVENTION = "PREVENTION"
    VULNERABILITY = "VULNERABILITY"


class InjectExecutionActions(str, Enum):
    """Execution action phases used by injection signatures."""

    PREREQUISITE_CHECK = "prerequisite_check"
    PREREQUISITE_EXECUTION = "prerequisite_execution"
    CLEANUP_EXECUTION = "cleanup_execution"
    COMMAND_EXECUTION = "command_execution"
    DNS_RESOLUTION = "dns_resolution"
    FILE_EXECUTION = "file_execution"
    FILE_DROP = "file_drop"
    COMPLETE = "complete"


class MatchTypes(str, Enum):
    """Supported match algorithm types for signature evaluation."""

    MATCH_TYPE_FUZZY = "fuzzy"
    MATCH_TYPE_SIMPLE = "simple"


class SignatureTypes(str, Enum):
    """Supported signature field identifiers."""

    SIG_TYPE_PARENT_PROCESS_NAME = "parent_process_name"
    SIG_TYPE_SOURCE_IPV4_ADDRESS = "source_ipv4_address"
    SIG_TYPE_SOURCE_IPV6_ADDRESS = "source_ipv6_address"
    SIG_TYPE_TARGET_IPV4_ADDRESS = "target_ipv4_address"
    SIG_TYPE_TARGET_IPV6_ADDRESS = "target_ipv6_address"
    SIG_TYPE_TARGET_HOSTNAME_ADDRESS = "target_hostname_address"
    SIG_TYPE_START_DATE = "start_date"
    SIG_TYPE_END_DATE = "end_date"
    SIG_TYPE_CLOUD_PROVIDER = "cloud_provider"
    SIG_TYPE_CLOUD_ACCOUNT_ID = "cloud_account_id"
    SIG_TYPE_CLOUD_REGION = "cloud_region"
    SIG_TYPE_TARGET_SERVICE = "target_service"
    SIG_TYPE_QUERY = "query"
