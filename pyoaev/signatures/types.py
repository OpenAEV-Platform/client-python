from enum import Enum


class ExpectationType(str, Enum):
    DETECTION = "DETECTION"
    PREVENTION = "PREVENTION"
    VULNERABILITY = "VULNERABILITY"


class ExecutionStatus(str, Enum):
    EXECUTED = "EXECUTED"
    EXECUTED_WITH_CLEANUP_FAILURE = "EXECUTED_WITH_CLEANUP_FAILURE"
    WARNING = "WARNING"
    ACCESS_DENIED = "ACCESS_DENIED"
    ERROR = "ERROR"
    COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
    COMMAND_CANNOT_BE_EXECUTED = "COMMAND_CANNOT_BE_EXECUTED"
    PREREQUISITE_FAILED = "PREREQUISITE_FAILED"
    INVALID_USAGE = "INVALID_USAGE"
    TIMEOUT = "TIMEOUT"
    INTERRUPTED = "INTERRUPTED"
    ASSET_AGENTLESS = "ASSET_AGENTLESS"
    AGENT_INACTIVE = "AGENT_INACTIVE"
    AGENT_OVERLOADED = "AGENT_OVERLOADED"
    INFO = "INFO"
    PARTIAL = "PARTIAL"
    MAYBE_PREVENTED = "MAYBE_PREVENTED"
    MAYBE_PARTIAL_PREVENTED = "MAYBE_PARTIAL_PREVENTED"


class InjectExecutionActions(str, Enum):
    PREREQUISITE_CHECK = "prerequisite_check"
    PREREQUISITE_EXECUTION = "prerequisite_execution"
    CLEANUP_EXECUTION = "cleanup_execution"
    COMMAND_EXECUTION = "command_execution"
    DNS_RESOLUTION = "dns_resolution"
    FILE_EXECUTION = "file_execution"
    FILE_DROP = "file_drop"
    COMPLETE = "complete"


class MatchTypes(str, Enum):
    MATCH_TYPE_FUZZY = "fuzzy"
    MATCH_TYPE_SIMPLE = "simple"


class SignatureTypes(str, Enum):
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
    # AI adversarial validation: correlate AI defense (LLM firewall / guardrail) events back to a
    # specific AI inject execution.
    SIG_TYPE_AI_REQUEST_MARKER = "ai_request_marker"
    SIG_TYPE_AI_TARGET_ENDPOINT = "ai_target_endpoint"
